# Rolling Buffer Wake Word Detection Strategy

## Objective
Change the wake word detection strategy in `main.py` to use a **5-second rolling buffer**, tested **every 1 second**. This replaces the current continuous streaming verification.

## Current Implementation
The current `main.py` reads audio in small chunks (1280 samples) and feeds them directly to `model.predict()`. This is a standard streaming approach where the model maintains internal state across chunks.

## New Strategy
1.  **Audio Buffering**:
    *   Maintain a rolling buffer of the last **5 seconds** of audio.
    *   Continue reading from the microphone in small chunks (to ensure low latency in capture), but accumulate them into the buffer.

2.  **Periodic Testing**:
    *   Instead of checking for the wake word on every chunk, perform a check only **once every second**.

3.  **Detection Logic**:
    *   At each 1-second interval:
        1.  Extract the most recent 5 seconds of audio from the buffer.
        2.  **Reset** the model's internal state to ensure independent analysis of this window.
        3.  Run the model on this 5-second clip (using `model.predict_clip` or by feeding chunks after reset).
        4.  Evaluate the predictions returned for the clip.

## Implementation Plan

### 1. Update `WakeWordDetector` Class

#### Initialization (`__init__`)
*   Add a buffer to store audio history.
    *   `self.audio_buffer = collections.deque(maxlen=80000)` (approx 5 seconds at 16kHz).
    *   Alternatively, use a bytearray or list and manage size manually if `deque` doesn't support slicing efficiently for numpy conversion. A `collections.deque` of chunks (numpy arrays) might be better, concatenating them when needed.
*   Add a timer variable: `self.last_check_time = time.time()`.

#### Audio Loop (`run`)
*   The `audio_queue` processing loop will:
    1.  Receive new chunk from queue.
    2.  Append chunk to `self.audio_buffer`.
    3.  Trim buffer to keep only the last 5 seconds (if using list/bytearray).
    4.  Check if `current_time - self.last_check_time >= 1.0` seconds.
    5.  If time to check:
        *   Update `self.last_check_time`.
        *   Convert buffer to single numpy array: `buffer_array = np.concatenate(self.audio_buffer)`.
        *   Call `self.process_buffer(buffer_array)`.

#### Processing Method (`process_buffer`)
*   **Input**: 5-second numpy audio array.
*   **Steps**:
    1.  `self.model.reset()`: Clear internal state (RNN buffers).
    2.  `predictions = self.model.predict_clip(buffer_array)`: Run inference on the full clip.
    3.  Iterate through `predictions` (list of dicts) to find if any score exceeds `self.threshold`.
    4.  If detected:
        *   Trigger video playback.
        *   **Crucial**: After playback, clear the buffer and reset the model again to avoid re-triggering on the same audio immediately.

### 2. Handling "Rolling" Nature
*   Using `predict_clip` on overlapping windows (0-5s, 1-6s, etc.) effectively tests the wake word at different offsets.
*   Since we reset the model each time, we treat each 5-second window as an isolated audio clip.

### 3. Edge Cases
*   **Buffer not full**: Skip detection until we have at least X seconds (e.g., 2-3 seconds) of audio.
*   **Performance**: `predict_clip` on 5 seconds of audio might take some time. Ensure it doesn't block the recording thread (it shouldn't, as recording is in a separate thread, but it might block the main loop processing queue). If processing > 1s, the queue might fill up. We should measure execution time.

## Definition of Done
*   [ ] `main.py` updated with rolling buffer logic.
*   [ ] Detection runs exactly once per second.
*   [ ] Model state is reset before each check.
*   [ ] System successfully triggers video on wake word.

