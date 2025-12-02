# Fix Wake Word Detection in main.py

## Problem Analysis

Comparing `main.py` and `test_wakeword_file.py`, the wake word detection fails in `main.py` due to a processing rate mismatch caused by an artificial delay.

### 1. The Rate Mismatch
- **Input Rate**: The audio stream is configured for 16kHz. `openwakeword` processes chunks of 1280 samples.
  - Chunk Duration = $1280 / 16000 = 0.08$ seconds (80ms).
  - Audio chunks arrive every **80ms** (12.5 Hz).
- **Processing Rate**: The `main.py` loop includes `time.sleep(self.prediction_interval)` where `prediction_interval` defaults to **0.1s** (100ms).
  - The loop processes at most one chunk every **100ms** (10 Hz).

### 2. The Consequence
Because the consumer (processing loop) is slower than the producer (microphone input), the following happens:
1.  **Latency Buildup**: The system falls behind by 20ms for every chunk received. After 4 seconds of operation, it is 1 second behind reality.
2.  **Queue Overflow**: The `audio_queue` (size 100) fills up in about 30-40 seconds.
3.  **Dropped Packets**: Once the queue is full, the `_recording_worker` (lines 284-288) starts dropping incoming audio chunks because the queue is full.
4.  **Broken Stream**: The model receives a discontinuous stream of audio (chunks are missing). Wake word detection models rely on continuous temporal patterns (e.g., "Hey" followed immediately by "Jarvis"). Dropped frames destroy this pattern.

### Why `test_wakeword_file.py` works
The test script reads the file and processes chunks sequentially without any `sleep`. It feeds the model as fast as the CPU allows, maintaining the correct sequence of audio frames.

The fact that the *recorded files* worked suggests that either:
- The tests were short enough that the queue didn't overflow yet (so no dropped frames in the file).
- Or the user got lucky with where the drops occurred.
However, the live system would suffer from massive latency (up to 8 seconds) before dropping frames, making it appear broken to the user even before the drops start.

## Plan to Fix

1.  **Remove Artificial Delay**:
    - Delete `time.sleep(self.prediction_interval)` from the main processing loop in `main.py`.
    - The loop should run as fast as `audio_queue.get()` returns data. Since `get()` blocks until data is available, the loop will naturally sync with the audio stream (every 80ms).

2.  **Cleanup Configuration**:
    - Remove `PREDICTION_INTERVAL` from initialization and env var loading, as it is harmful.

3.  **Refine Audio Handling** (Optional but recommended):
    - The `audio_buffer` deque (lines 349-350) is effectively redundant because the code only ever uses `audio_buffer[-1]` (the current chunk).
    - Simplify the loop to pass `current_audio` directly from the queue to the model.

4.  **Verification**:
    - Run the modified `main.py`.
    - Verify that CPU usage is acceptable (it should be, as `get()` is blocking/efficient).
    - Verify that detection triggers immediately upon speaking.

