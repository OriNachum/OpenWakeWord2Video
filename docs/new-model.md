To create a custom wake word (e.g., "Hey Computer," "Beam me up," etc.), you cannot simply type it into the config. You must **train a new model file** specifically for that phrase.

The good news is that `openWakeWord` has an automated system that does this for you in about 45-60 minutes using free Google cloud servers.

### Step 1: Train Your Model (The Easy Way)

You do not need to install complex training software on your Mac or Pi. Use the official Google Colab notebook:

1.  **Open this link:** [Official openWakeWord Training Notebook](https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb?usp=sharing)
2.  **Sign in** with a Google account.
3.  **Scroll down** to the first section ("1. Test Example Training Clip Generation").
4.  **Enter your desired phrase** in the `target_word` box (e.g., `hey_computer`).
5.  **Press the "Play" button** next to that cell to hear how the AI pronounces it.
      * *Tip:* If it pronounces it wrong, try phonetic spelling (e.g., instead of "Read", try "Reed").
6.  **Go to the top menu:** Click **Runtime** -\> **Run all**.
7.  **Wait \~60 minutes.** Keep the tab open.
8.  **Download:** When finished, it will automatically download a file named something like `my_custom_model.tflite` (or you can find it in the file folder icon on the left sidebar).

### Step 2: Add the Model to Your Project

Once you have your file (let's call it `hey_computer.tflite`):

1.  **Copy the file** into the same folder as your Python script.
2.  **Update your `.env` file** to point to the **filename** instead of a default name.

<!-- end list -->

```ini
# .env

# Point to your custom file path
WAKE_WORD_MODELS=./hey_computer.tflite

VIDEO_PATH=./video.mp4
THRESHOLD=0.5
```

### Step 3: Run Your Script

You don't need to change any Python code. The `openwakeword` library is smart enough to detect that you provided a file path ending in `.tflite` (or `.onnx`) and will load it automatically.

```bash
python3 your_script.py
```

### Important Notes

  * **Accuracy:** Custom models trained this way are surprisingly good, but might be slightly less robust than the massive pre-trained ones ("Hey Jarvis", etc.).
  * **False Positives:** If it triggers too often, increase your `THRESHOLD` in the `.env` file to `0.6` or `0.7`.
  * **Pi Compatibility:** The `.tflite` file you get from the notebook is perfect for the Raspberry Pi setup we discussed.