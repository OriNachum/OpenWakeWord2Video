#!/usr/bin/env python3
"""
Microphone Testing Utility

This script helps you:
1. List all available audio input devices
2. Test recording from a specific device
3. Verify audio quality
"""

import pyaudio
import wave
import numpy as np
import sys


def list_devices():
    """List all available audio input devices."""
    print("\n" + "=" * 60)
    print("Available Audio Input Devices")
    print("=" * 60)
    
    audio = pyaudio.PyAudio()
    
    input_devices = []
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            input_devices.append((i, info))
            print(f"\nDevice {i}: {info['name']}")
            print(f"  Max Input Channels: {info['maxInputChannels']}")
            print(f"  Default Sample Rate: {int(info['defaultSampleRate'])} Hz")
    
    audio.terminate()
    
    if not input_devices:
        print("\n⚠️  No input devices found!")
        return None
    
    print("\n" + "=" * 60)
    return input_devices


def test_recording(device_index=None, duration=5):
    """Record a test sample and save it."""
    print("\n" + "=" * 60)
    print(f"Recording {duration}-second test sample...")
    print("=" * 60)
    
    # Audio configuration
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    audio = pyaudio.PyAudio()
    
    try:
        # Open stream
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        print(f"\n🎤 Recording from device {device_index if device_index else 'default'}...")
        print("Speak into your microphone!")
        
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            # Show progress
            progress = (i + 1) / (RATE / CHUNK * duration)
            bar_length = 30
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\r[{bar}] {int(progress * 100)}%", end="", flush=True)
        
        print("\n✅ Recording complete!")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        
        # Save to file
        output_filename = "test_recording.wav"
        wf = wave.open(output_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"💾 Saved recording to: {output_filename}")
        print(f"   You can play it with: mpv {output_filename}")
        
        # Analyze audio level
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        avg_amplitude = np.abs(audio_data).mean()
        max_amplitude = np.abs(audio_data).max()
        
        print(f"\n📊 Audio Analysis:")
        print(f"   Average amplitude: {avg_amplitude:.0f}")
        print(f"   Maximum amplitude: {max_amplitude}")
        print(f"   Max possible: 32768")
        
        if avg_amplitude < 100:
            print("\n⚠️  Warning: Audio level is very low!")
            print("   Check your microphone volume settings")
        elif avg_amplitude > 10000:
            print("\n⚠️  Warning: Audio level is very high!")
            print("   Consider reducing microphone gain")
        else:
            print("\n✅ Audio levels look good!")
    
    except Exception as e:
        print(f"\n❌ Error during recording: {e}")
    
    finally:
        audio.terminate()


def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("Microphone Testing Utility")
    print("=" * 60)
    
    # List devices
    devices = list_devices()
    
    if not devices:
        return
    
    # Ask user what to do
    print("\nOptions:")
    print("  1. Test recording with default device")
    print("  2. Test recording with specific device")
    print("  3. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            test_recording(duration=5)
        elif choice == "2":
            device_idx = input("Enter device number: ").strip()
            try:
                device_idx = int(device_idx)
                test_recording(device_index=device_idx, duration=5)
            except ValueError:
                print("❌ Invalid device number")
        elif choice == "3":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()


