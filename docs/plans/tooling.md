# Tooling & Debugging Improvements Plan

This document outlines the plan to add diagnostic tooling and debugging features to the Wake Word application.

## 1. Rolling Audio Buffer Recording

**Goal:** Enable continuous recording of the audio stream into a rolling buffer of files to analyze what the model "heard" leading up to an event (or failure).

### Requirements
- Save the last 10 files.
- Each file should contain 5 seconds of audio.
- Rolling buffer: Oldest file is overwritten when the limit is reached.
- Configurable via environment variables (enabled/disabled).

### Technical Design

**New Class: `RollingAudioRecorder`**
- **Responsibilities**:
    - Accumulate audio chunks.
    - Write chunks to WAV files every 5 seconds.
    - Manage file rotation (0-9).
- **Integration**:
    - Instantiated in `WakeWordDetector` if enabled.
    - Called within the main run loop: `recorder.add_audio(audio_chunk)`.
- **Output**:
    - Directory: `debug_recordings/` (created on startup).
    - Files: `buffer_0.wav`, `buffer_1.wav`, ..., `buffer_9.wav`.
    - Format: 16kHz, Mono, 16-bit PCM (same as input).

**Configuration (`.env`)**
- `ENABLE_DEBUG_RECORDING`: `true` / `false` (default: `false`)
- `DEBUG_RECORDING_PATH`: Path to save files (default: `./debug_recordings`)

**Data Flow Change in `main.py`**:
```python
# In main loop
audio_data = self.audio_queue.get()
# ... existing prediction logic ...

# New recording logic
if self.debug_recorder:
    self.debug_recorder.process_chunk(audio_data)
```

## 2. Wake Word File Tester

**Goal:** Verify if the wake word model works correctly on a pre-recorded audio file. This allows for reproducible testing without needing to speak into the microphone repeatedly.

### Requirements
- Standalone script.
- Input: Path to a WAV file.
- Process: Run the same `openwakeword` inference on the file contents.
- Output: Timestamp and confidence score of detections.

### Technical Design

**New Script: `test_wakeword_file.py`**
- **Usage**: `python test_wakeword_file.py <path_to_file.wav>`
- **Logic**:
    1. Load `openwakeword` models (using same config as main app).
    2. Read the input WAV file.
    3. Validate format (must be 16kHz, mono). If not, warn or convert (optional, start with warn).
    4. Iterate through the audio in chunks (1280 samples).
    5. Feed chunks to `model.predict()`.
    6. Print detections with timestamps (e.g., "00:04.5 - Detected 'hey_jarvis' (0.85)").

## Implementation Tasks

### Phase 1: Rolling Recorder
1. [ ] Create `RollingAudioRecorder` class in `main.py` (or separate utility file).
2. [ ] Implement logic to buffer chunks and write to WAV using `wave` module.
3. [ ] Implement file rotation logic (index 0-9).
4. [ ] Integrate into `WakeWordDetector.run()` loop.
5. [ ] Add environment variable parsing for configuration.

### Phase 2: File Tester Script
1. [ ] Create `test_wakeword_file.py`.
2. [ ] Implement model loading (refactor model loading from `main.py` if needed to avoid code duplication, or just copy logic for now to keep `main.py` self-contained).
3. [ ] Implement WAV file reading and chunking loop.
4. [ ] Add reporting of detections.

## Future Considerations
- **Resampling**: `test_wakeword_file.py` could automatically resample input audio to 16kHz if it differs.
- **Visualizer**: Generate a plot of confidence scores over time for the tested file.

