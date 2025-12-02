# Wake Word Video Trigger App Plan

This document outlines the design and implementation plan for a Python application running on Unix that listens for a specific wake-up word and plays a local video file when triggered.

## 1. Overview

The application will:
1.  Continuously listen to audio input from a USB microphone.
2.  Analyze the audio stream in real-time to detect a predefined wake word.
3.  Trigger a video playback action upon detection.
4.  Resume listening after the video finishes (or concurrently, depending on requirements).

## 2. Technology Stack

### 2.1 Wake Word Detection
We will use **OpenWakeWord** as the primary choice because it is open-source, offline, and free (no API key required).
*   **Alternative**: **Porcupine (Picovoice)** - Highly accurate, lightweight, but requires an AccessKey (free tier available).

### 2.2 Audio Input
*   **Library**: `pyaudio` or `sounddevice`.
*   `pyaudio` is the standard for real-time audio processing in Python.

### 2.3 Video Playback
*   **Tool**: `mpv` or `vlc`.
*   **Integration**: `subprocess` module to call the system's media player, or `python-mpv` / `python-vlc` for tighter integration.
*   **Reasoning**: Calling a robust external player like `mpv` is the most reliable way to handle various video formats and audio syncing on Unix without building a full GUI.

## 3. Architecture

```mermaid
graph TD
    A[Microphone Input] -->|Raw Audio Stream| B(Audio Buffer)
    B -->|Chunks| C{Wake Word Engine}
    C -- Detected --> D[Trigger Action]
    D --> E[Play Video (MPV)]
    E -- Finished --> B
    C -- Not Detected --> B
```

## 4. Implementation Steps

### Step 1: Environment Setup
*   Create a Python virtual environment.
*   Install system dependencies:
    ```bash
    # Ubuntu/Debian
    sudo apt-get install python3-pyaudio libportaudio2 mpv
    # macOS
    brew install portaudio mpv
    ```
*   Install Python libraries:
    ```txt
    pyaudio
    openwakeword
    numpy
    ```

### Step 2: Audio Input Verification
*   Write a simple script to list available microphones.
*   Verify the USB microphone index.
*   Record a 5-second sample to ensure audio quality.

### Step 3: Wake Word Detection Prototype
*   Implement a loop using `openwakeword` to process audio chunks (typically 1280 samples).
*   Print "Wake Word Detected" to the console when the threshold is met.

### Step 4: Video Playback Integration
*   Create a function `play_video(path)` using `subprocess.run(["mpv", "--fs", path])`.
*   The `--fs` flag ensures fullscreen playback.
*   Ensure the player closes automatically after playback.

### Step 5: Main Application Loop
*   Combine the audio loop and video trigger.
*   **Logic**:
    ```python
    import pyaudio
    import numpy as np
    from openwakeword.model import Model
    import subprocess

    # Load Model
    owwModel = Model(wakeword_models=["hey_jarvis"]) 

    # Audio Stream
    mic = pyaudio.PyAudio()
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1280)

    while True:
        # Get Audio
        audio = np.frombuffer(stream.read(1280), dtype=np.int16)
        
        # Predict
        prediction = owwModel.predict(audio)
        
        # Check
        if prediction["hey_jarvis"] > 0.5:
            print("Wake word detected!")
            # Pause listening (optional)
            subprocess.run(["mpv", "--fs", "video.mp4"])
            # Resume listening
            # Reset buffer if necessary to avoid backlog
            stream.read(stream.get_read_available()) 
    ```

## 5. Configuration & Customization

*   **Config File**: Use a `.env` or `config.yaml` to store:
    *   Wake Word Model (e.g., "alexa", "hey_jarvis", or custom).
    *   Video File Path.
    *   Microphone Device Index (optional, auto-detect default).
    *   Sensitivity Threshold.

## 6. Deployment on Unix
*   Create a `systemd` service (Linux) or `launchd` agent (macOS) to run the script on boot.
*   Ensure the user has permissions to access audio and video devices.

## 7. Future Improvements
*   **Randomized Videos**: Pick a random video from a folder.
*   **Smart Home Integration**: Trigger webhook calls in addition to playing video.
*   **Voice Commands**: Listen for specific commands after the wake word (requires Speech-to-Text like Whisper).

