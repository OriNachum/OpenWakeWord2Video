#!/usr/bin/env python3
"""
Wake Word File Tester

This script tests the wake word detection model on a pre-recorded audio file.
Useful for debugging and reproducible testing without live microphone input.

Usage:
    python test_wakeword_file.py <path_to_audio_file.wav>

Requirements:
    - Audio file must be in WAV format
    - Recommended: 16kHz sample rate, mono channel, 16-bit PCM
    - The script will warn if the format differs
"""

import sys
import os
import wave
import numpy as np
from dotenv import load_dotenv
import openwakeword
from openwakeword.model import Model

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"⚠️  Warning: Could not load .env file: {e}")


def format_timestamp(sample_index, sample_rate):
    """
    Convert sample index to human-readable timestamp.
    
    Args:
        sample_index: The sample number
        sample_rate: Audio sample rate (samples per second)
    
    Returns:
        Formatted string like "00:04.5" (MM:SS.s)
    """
    seconds = sample_index / sample_rate
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"


def validate_audio_format(wav_file):
    """
    Validate and display audio file format information.
    
    Args:
        wav_file: Open wave.Wave_read object
    
    Returns:
        tuple: (is_valid, needs_warning, info_message)
    """
    channels = wav_file.getnchannels()
    sample_width = wav_file.getsampwidth()
    framerate = wav_file.getframerate()
    n_frames = wav_file.getnframes()
    duration = n_frames / framerate
    
    info_lines = [
        f"  Channels: {channels} ({'Mono' if channels == 1 else 'Stereo' if channels == 2 else 'Multi'})",
        f"  Sample Rate: {framerate} Hz",
        f"  Sample Width: {sample_width} bytes ({sample_width * 8}-bit)",
        f"  Duration: {duration:.2f} seconds ({n_frames:,} frames)"
    ]
    
    # Check if format matches recommended specs
    needs_warning = False
    warnings = []
    
    if framerate != 16000:
        warnings.append(f"⚠️  Sample rate is {framerate} Hz (recommended: 16000 Hz)")
        needs_warning = True
    
    if channels != 1:
        warnings.append(f"⚠️  Audio has {channels} channels (recommended: 1/mono)")
        needs_warning = True
    
    if sample_width != 2:
        warnings.append(f"⚠️  Sample width is {sample_width} bytes (recommended: 2 bytes/16-bit)")
        needs_warning = True
    
    return True, needs_warning, "\n".join(info_lines), warnings


def load_audio_file(file_path):
    """
    Load and validate a WAV audio file.
    
    Args:
        file_path: Path to the WAV file
    
    Returns:
        tuple: (audio_data as numpy array, sample_rate, success)
    """
    try:
        with wave.open(file_path, 'rb') as wav_file:
            # Validate format
            is_valid, needs_warning, info, warnings = validate_audio_format(wav_file)
            
            print("\n📄 Audio File Information:")
            print(info)
            
            if needs_warning:
                print("\n⚠️  Format Warnings:")
                for warning in warnings:
                    print(f"  {warning}")
                print("\n  Note: The model expects 16kHz, mono, 16-bit audio.")
                print("        Results may be inaccurate with different formats.\n")
            
            # Read audio data
            frames = wav_file.readframes(wav_file.getnframes())
            
            # Convert to numpy array
            if wav_file.getsampwidth() == 2:
                # 16-bit audio
                audio_data = np.frombuffer(frames, dtype=np.int16)
            elif wav_file.getsampwidth() == 1:
                # 8-bit audio - convert to 16-bit
                audio_data = np.frombuffer(frames, dtype=np.uint8).astype(np.int16)
                audio_data = (audio_data - 128) * 256
            elif wav_file.getsampwidth() == 4:
                # 32-bit audio - convert to 16-bit
                audio_data = np.frombuffer(frames, dtype=np.int32).astype(np.int16)
            else:
                print(f"❌ Unsupported sample width: {wav_file.getsampwidth()} bytes")
                return None, None, False
            
            # Handle stereo by taking only the first channel
            if wav_file.getnchannels() == 2:
                print("  Converting stereo to mono (using left channel)...")
                audio_data = audio_data[::2]
            elif wav_file.getnchannels() > 2:
                print(f"  Converting {wav_file.getnchannels()} channels to mono (using first channel)...")
                audio_data = audio_data[::wav_file.getnchannels()]
            
            sample_rate = wav_file.getframerate()
            
            return audio_data, sample_rate, True
    
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        return None, None, False
    except wave.Error as e:
        print(f"❌ Error: Invalid WAV file: {e}")
        return None, None, False
    except Exception as e:
        print(f"❌ Error loading audio file: {e}")
        import traceback
        traceback.print_exc()
        return None, None, False


def test_wake_word_on_file(file_path, wake_word_models=None, threshold=0.5):
    """
    Test wake word detection on a pre-recorded audio file.
    
    Args:
        file_path: Path to the audio file
        wake_word_models: List of model names (uses env var if None)
        threshold: Detection threshold (uses env var if None)
    """
    print("=" * 70)
    print("Wake Word File Tester")
    print("=" * 70)
    
    # Load configuration
    if wake_word_models is None:
        wake_word_models = os.getenv("WAKE_WORD_MODELS", "hey_jarvis").split(",")
    
    if threshold is None:
        threshold = float(os.getenv("THRESHOLD", "0.5"))
    
    print(f"\n🔧 Configuration:")
    print(f"  Models: {', '.join(wake_word_models)}")
    print(f"  Threshold: {threshold}")
    print(f"  Input File: {file_path}")
    
    # Load audio file
    audio_data, sample_rate, success = load_audio_file(file_path)
    if not success:
        return
    
    print(f"\n✅ Audio file loaded successfully")
    print(f"  Total samples: {len(audio_data):,}")
    
    # Load wake word model
    print("\n🔄 Loading wake word model...")
    try:
        # Download models if needed
        try:
            openwakeword.utils.download_models(wake_word_models)
        except Exception as e:
            print(f"⚠️  Warning: Could not download models: {e}")
        
        # Load model
        model = Model(
            wakeword_models=wake_word_models,
            inference_framework="onnx"
        )
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Process audio in chunks
    print("\n🔍 Processing audio...")
    print("=" * 70)
    
    chunk_size = 1280  # OpenWakeWord expects 1280 samples per chunk
    num_chunks = len(audio_data) // chunk_size
    detections = []
    
    # Debug: check audio levels
    max_amplitude = np.max(np.abs(audio_data))
    
    max_scores = {}

    # For grouping consecutive detections
    current_event = None  # {start_idx, end_idx, max_score, model_name}
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size
        chunk = audio_data[start_idx:end_idx]
        
        # Run prediction
        prediction = model.predict(chunk)
        
        # Check predictions
        chunk_detected = False
        best_model_in_chunk = None
        best_score_in_chunk = 0
        
        for model_name, score in prediction.items():
            # Track max score overall
            if model_name not in max_scores:
                max_scores[model_name] = 0.0
            if score > max_scores[model_name]:
                max_scores[model_name] = score

            if score > threshold:
                chunk_detected = True
                if score > best_score_in_chunk:
                    best_score_in_chunk = score
                    best_model_in_chunk = model_name
        
        # Grouping logic
        if chunk_detected:
            if current_event is None:
                # Start new event
                current_event = {
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'max_score': best_score_in_chunk,
                    'model_name': best_model_in_chunk,
                    'start_time': format_timestamp(start_idx, sample_rate)
                }
            else:
                # Update existing event
                current_event['end_idx'] = end_idx
                if best_score_in_chunk > current_event['max_score']:
                    current_event['max_score'] = best_score_in_chunk
                    current_event['model_name'] = best_model_in_chunk # Update to best model in sequence
        else:
            if current_event:
                # End event
                duration = (current_event['end_idx'] - current_event['start_idx']) / sample_rate
                timestamp = current_event['start_time']
                model_name = current_event['model_name']
                score = current_event['max_score']
                
                detections.append(current_event)
                print(f"🎯 {timestamp} - Detected '{model_name}' (duration: {duration:.2f}s, max conf: {score:.3f})")
                current_event = None

    # Handle event ending at file end
    if current_event:
        duration = (current_event['end_idx'] - current_event['start_idx']) / sample_rate
        timestamp = current_event['start_time']
        model_name = current_event['model_name']
        score = current_event['max_score']
        detections.append(current_event)
        print(f"🎯 {timestamp} - Detected '{model_name}' (duration: {duration:.2f}s, max conf: {score:.3f})")

    # Summary
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"  Total chunks processed: {num_chunks}")
    print(f"  Events found: {len(detections)}")
    
    for model_name, max_score in max_scores.items():
        print(f"  Max score for '{model_name}': {max_score:.6f}")
    
    print("\n✅ Testing complete")


import argparse

def main():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(description="Test wake word detection on a pre-recorded audio file.")
    parser.add_argument("file_path", help="Path to the audio file (WAV format)")
    parser.add_argument("threshold", nargs="?", type=float, help="Detection threshold (default: 0.5 or env var)")
    parser.add_argument("--models", help="Comma-separated list of wake word models to test (overrides env var)")

    args = parser.parse_args()
    
    file_path = args.file_path
    threshold = args.threshold
    
    # Parse models argument if provided
    wake_word_models = None
    if args.models:
        wake_word_models = [m.strip() for m in args.models.split(",")]
    
    # Run the test
    test_wake_word_on_file(file_path, wake_word_models=wake_word_models, threshold=threshold)


if __name__ == "__main__":
    main()

