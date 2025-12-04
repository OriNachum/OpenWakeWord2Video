#!/usr/bin/env python3
"""
Wake Word Video Trigger Application - Auto-Detect Fix
"""

from dotenv import load_dotenv
import os
import sys
import subprocess
import time
import threading
from queue import Queue, Empty
from collections import deque
import wave
import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model

# Load environment variables
load_dotenv()

class RollingAudioRecorder:
    """
    Records audio in a rolling buffer of files for debugging purposes.
    Maintains the last N files, each containing a fixed duration of audio.
    """
    def __init__(self, output_dir="./debug_recordings", num_files=10, 
                 duration_seconds=5, sample_rate=16000, channels=1):
        self.output_dir = output_dir
        self.num_files = num_files
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = 2
        self.samples_per_file = sample_rate * duration_seconds
        self.current_file_index = 0
        self.audio_buffer = []
        self.buffer_sample_count = 0
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_chunk(self, audio_data):
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        self.audio_buffer.append(audio_array)
        self.buffer_sample_count += len(audio_array)
        if self.buffer_sample_count >= self.samples_per_file:
            self._write_current_buffer()
    
    def _write_current_buffer(self):
        if not self.audio_buffer: return
        full_audio = np.concatenate(self.audio_buffer)
        audio_to_write = full_audio[:self.samples_per_file]
        filename = os.path.join(self.output_dir, f"buffer_{self.current_file_index}.wav")
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_to_write.tobytes())
        except Exception as e:
            print(f"⚠️  Warning: Failed to write debug audio file: {e}")
        self.current_file_index = (self.current_file_index + 1) % self.num_files
        if len(full_audio) > self.samples_per_file:
            remaining_audio = full_audio[self.samples_per_file:]
            self.audio_buffer = [remaining_audio]
            self.buffer_sample_count = len(remaining_audio)
        else:
            self.audio_buffer = []
            self.buffer_sample_count = 0


class WakeWordDetector:
    """Main class for wake word detection and video triggering."""
    
    def __init__(self, models_override=None, custom_model_path=None):
        """Initialize the wake word detector with configuration from environment."""
        # Custom ONNX model path takes precedence
        if custom_model_path:
            self.custom_model_path = custom_model_path
            self.wake_word_models = None
        elif os.getenv("CUSTOM_MODEL_PATH"):
            self.custom_model_path = os.getenv("CUSTOM_MODEL_PATH")
            self.wake_word_models = None
        else:
            self.custom_model_path = None
            if models_override:
                self.wake_word_models = models_override
            else:
                self.wake_word_models = os.getenv("WAKE_WORD_MODELS", "hey_jarvis").split(",")
            
        self.video_path = os.getenv("VIDEO_PATH", "./video.mp4")
        self.threshold = float(os.getenv("THRESHOLD", "0.5"))
        
        # Debug recording configuration
        self.enable_debug_recording = os.getenv("ENABLE_DEBUG_RECORDING", "false").lower() == "true"
        self.debug_recorder = None
        if self.enable_debug_recording:
            self.debug_recorder = RollingAudioRecorder()
        
        # Audio configuration
        self.sample_rate = 16000
        self.chunk_size = 1280  # OpenWakeWord expects 1280 samples per chunk
        self.format = pyaudio.paInt16
        self.channels = 1
        
        # Threading components
        self.audio_queue = Queue(maxsize=100) 
        self.recording = threading.Event()
        self.recording_thread = None
        
        # Components
        self.audio = None
        self.stream = None
        self.model = None
        
        print("=" * 60)
        print("Wake Word Video Trigger Application (Streaming Mode)")
        print("=" * 60)
        if self.custom_model_path:
            print(f"Custom Model: {self.custom_model_path}")
        else:
            print(f"Models: {self.wake_word_models}")
        print(f"Threshold: {self.threshold}")
        print("=" * 60)

    def verify_video_exists(self):
        if not os.path.exists(self.video_path):
            print(f"⚠️  Warning: Video file not found at {self.video_path}")
            return False
        return True
    
    def initialize_model(self):
        try:
            print("\n🔄 Loading wake word model...")
            if self.custom_model_path:
                # Verify custom model file exists
                if not os.path.exists(self.custom_model_path):
                    print(f"❌ Custom model file not found: {self.custom_model_path}")
                    return False
                print(f"Loading custom ONNX model from: {self.custom_model_path}")
                # ADDED: Explicitly pointing to embedding model just in case
                self.model = Model(wakeword_models=[self.custom_model_path], inference_framework="onnx")
            else:
                # Download and load pre-defined models
                openwakeword.utils.download_models(self.wake_word_models)
                self.model = Model(wakeword_models=self.wake_word_models, inference_framework="onnx")
            print("✅ Model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_audio(self):
        try:
            print("\n🔄 Initializing audio...")
            self.audio = pyaudio.PyAudio()
            
            # --- AUTO-DETECTION LOGIC START ---
            target_index = None
            print("Scanning for USB Microphone...")
            
            # List all devices to find the one named "USB PnP Audio Device"
            # This matches the name from your dmesg logs
            for i in range(self.audio.get_device_count()):
                dev_info = self.audio.get_device_info_by_index(i)
                dev_name = dev_info.get('name')
                print(f"  [{i}] {dev_name}")
                if "USB PnP" in dev_name:
                    target_index = i
                    print(f"  👉 FOUND IT! Using index {i}")
            
            if target_index is None:
                print("⚠️  Warning: 'USB PnP' not found by name. Trying default device.")
                # We do NOT set target_index, letting PyAudio pick system default
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=target_index, # Uses the auto-detected index
                frames_per_buffer=self.chunk_size
            )
            print("✅ Audio stream opened successfully")
            return True
        except Exception as e:
            print(f"❌ Error initializing audio: {e}")
            return False
    
    def play_video(self):
        try:
            print(f"\n🎬 Playing video: {self.video_path}")
            # Added --no-terminal to keep output clean
            subprocess.run(["mpv", "--fs", "--really-quiet", "--no-terminal", self.video_path], check=True)
            print("✅ Video playback completed")
        except FileNotFoundError:
            print("❌ Error: mpv not found.")
        except Exception as e:
            print(f"❌ Error playing video: {e}")
    
    def _recording_worker(self):
        print("🎙️  Recording thread started")
        while self.recording.is_set():
            try:
                # Added exception_on_overflow=False to prevent crashes if CPU is busy
                audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.audio_queue.put(audio_data, timeout=0.1)
            except Exception as e:
                # Fail silently on small buffer errors, print on big ones
                pass
        print("🎙️  Recording thread stopped")
    
    def start_recording(self):
        if not self.recording_thread or not self.recording_thread.is_alive():
            self.recording.set()
            self.recording_thread = threading.Thread(target=self._recording_worker, daemon=True)
            self.recording_thread.start()
    
    def stop_recording(self):
        self.recording.clear()
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)

    def run(self):
        """Main loop: Streaming inference."""
        if not self.verify_video_exists(): return
        if not self.initialize_model(): return
        if not self.initialize_audio(): return
        
        self.start_recording()
        
        print("\n🎤 Listening... (Streaming Mode)")
        
        try:
            while True:
                try:
                    # 1. Get audio chunk
                    audio_data = self.audio_queue.get(timeout=0.5)
                    
                    # 2. Debug Recording
                    if self.debug_recorder:
                        self.debug_recorder.process_chunk(audio_data)
                    
                    # 3. Convert to Numpy
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # 4. Run Inference (Added vad_threshold to save CPU!)
                    prediction = self.model.predict(audio_array, vad_threshold=0.5)
                    
                    # 5. Check Results
                    for model_name, score in prediction.items():
                        if score > self.threshold:
                            print(f"\n🎯 Wake word detected: {model_name} (Conf: {score:.2f})")
                            
                            self.stop_recording()
                            
                            # Clear old audio from queue so we don't process it later
                            with self.audio_queue.mutex:
                                self.audio_queue.queue.clear()
                            
                            self.model.reset()
                            self.play_video()
                            
                            print("\n🎤 Listening again...")
                            self.start_recording()
                            
                except Empty:
                    continue
        
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        finally:
            self.cleanup()

    def cleanup(self):
        self.stop_recording()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

import argparse

def main():
    parser = argparse.ArgumentParser(description="Wake Word Video Trigger Application")
    parser.add_argument("--models", help="Comma-separated list of wake word models")
    parser.add_argument("--model-path", help="Path to custom ONNX model file (overrides --models)")
    args = parser.parse_args()
    
    models_override = [m.strip() for m in args.models.split(",")] if args.models else None
    detector = WakeWordDetector(
        models_override=models_override,
        custom_model_path=args.model_path
    )
    detector.run()

if __name__ == "__main__":
    main()
