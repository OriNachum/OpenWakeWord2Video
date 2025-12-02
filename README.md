# Wake Word Video Trigger Application

A Python application that continuously listens for a wake-up word using a USB microphone and triggers video playback when detected. Built for Unix systems (macOS/Linux).

## Features

- 🎤 **Continuous Wake Word Detection** - Uses OpenWakeWord for offline, real-time detection
- 🎬 **Automatic Video Playback** - Triggers fullscreen video playback on detection
- 🔧 **Configurable** - Easy configuration via `.env` file
- 🆓 **Completely Free** - No API keys or cloud services required
- 🖥️ **Unix-Friendly** - Designed for macOS and Linux systems

## Prerequisites

### System Dependencies

#### macOS
```bash
brew install portaudio mpv
sudo apt-get install libspeexdsp-dev
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio libportaudio2 mpv libspeexdsp-dev
pip install https://github.com/dscripka/openWakeWord/releases/download/v0.1.1/speexdsp_ns-0.1.2-cp38-cp38-linux_x86_64.whl

```

### Python Requirements

- Python 3.8 or higher
- USB microphone connected to your system

## Installation

1. **Clone or navigate to the repository:**
   ```bash
   cd /path/to/sim-patiach
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create your configuration file:**
   ```bash
   cp .sample.env .env
   ```

5. **Edit `.env` with your settings:**
   ```bash
   nano .env  # or use your preferred editor
   ```

## Configuration

Edit the `.env` file with the following settings:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `WAKE_WORD_MODELS` | Wake word model(s) to use (comma-separated) | `hey_jarvis` | `hey_jarvis` or `alexa,hey_jarvis` |
| `VIDEO_PATH` | Path to the video file to play | `./video.mp4` | `/path/to/video.mp4` |
| `DEVICE_INDEX` | Microphone device index (leave empty for default) | _(empty)_ | `1` |
| `THRESHOLD` | Detection sensitivity (0.0-1.0, higher = less sensitive) | `0.5` | `0.6` |
| `PREDICTION_INTERVAL` | Sleep time between predictions in seconds | `0.1` | `0.05` or `0.2` |

### Available Wake Word Models

OpenWakeWord includes several built-in models:
- `hey_jarvis` - "Hey Jarvis"
- `alexa` - "Alexa"
- `hey_mycroft` - "Hey Mycroft"
- `hey_rhasspy` - "Hey Rhasspy"

You can also train custom models - see [OpenWakeWord documentation](https://github.com/dscripka/openWakeWord).

## Usage

### Step 1: Test Your Microphone

Before running the main application, verify your microphone setup:

```bash
python test_microphone.py
```

This utility will:
- List all available input devices
- Help you identify your USB microphone's device index
- Record a test sample to verify audio quality
- Analyze audio levels

If your USB microphone isn't the default device, note its device index and add it to your `.env` file:
```
DEVICE_INDEX=2  # Replace with your device number
```

### Step 2: Prepare Your Video

Make sure you have a video file ready and update the `VIDEO_PATH` in your `.env` file:

```bash
# Example paths
VIDEO_PATH=./my_video.mp4
# or
VIDEO_PATH=/Users/username/Videos/response.mp4
```

### Step 3: Run the Application

```bash
python main.py
```

The application will:
1. Load the wake word detection model
2. Open your microphone stream
3. Display available audio devices
4. Start listening for the wake word

When the wake word is detected:
- The console will show "Wake word detected!" with confidence score
- The video will play in fullscreen
- After video completion, listening resumes automatically

### Stopping the Application

Press `Ctrl+C` to stop the application gracefully.

## Troubleshooting

### "Error initializing audio"

**Issue:** PyAudio can't access the microphone.

**Solutions:**
- Verify your USB microphone is connected: `python test_microphone.py`
- Check system permissions (macOS requires microphone access permission)
- Try specifying a different `DEVICE_INDEX` in `.env`

### "mpv not found"

**Issue:** Video player not installed.

**Solution:**
```bash
# macOS
brew install mpv

# Ubuntu/Debian
sudo apt-get install mpv
```

### Wake word not detecting

**Issue:** Application doesn't respond to wake word.

**Solutions:**
- Lower the `THRESHOLD` in `.env` (try `0.3` or `0.4`)
- Speak more clearly and closer to the microphone
- Test microphone levels with `python test_microphone.py`
- Try a different wake word model

### Wake word too sensitive (false positives)

**Issue:** Application triggers on background noise.

**Solutions:**
- Increase the `THRESHOLD` in `.env` (try `0.6` or `0.7`)
- Reduce microphone gain in system settings
- Position microphone away from speakers/noise sources

### Video file not found

**Issue:** "Warning: Video file not found"

**Solution:**
- Verify the path in `VIDEO_PATH` is correct
- Use absolute paths for reliability
- Ensure the file exists: `ls -la /path/to/video.mp4`

## Advanced Usage

### Running on System Startup (macOS - launchd)

1. Create a launchd plist file at `~/Library/LaunchAgents/com.user.wakeword.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.wakeword</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/sim-patiach/venv/bin/python</string>
        <string>/path/to/sim-patiach/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/sim-patiach</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

2. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.user.wakeword.plist
```

### Running on System Startup (Linux - systemd)

1. Create a systemd service file at `/etc/systemd/system/wakeword.service`:

```ini
[Unit]
Description=Wake Word Video Trigger
After=sound.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/sim-patiach
ExecStart=/path/to/sim-patiach/venv/bin/python /path/to/sim-patiach/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:
```bash
sudo systemctl enable wakeword.service
sudo systemctl start wakeword.service
```

### Multiple Video Files (Random Selection)

To play a random video from a folder, modify the `VIDEO_PATH` approach:

1. Create a folder with multiple videos: `/path/to/videos/`
2. Update `main.py` to select randomly (or create a playlist feature)

## Project Structure

```
sim-patiach/
├── main.py                 # Main application
├── test_microphone.py      # Microphone testing utility
├── requirements.txt        # Python dependencies
├── .sample.env            # Sample configuration
├── .env                   # Your configuration (not in git)
├── init_env.sh            # Environment setup script (optional)
├── init_env.ps1           # PowerShell setup script (optional)
└── docs/
    └── plans/
        └── wakeup-word.md # Design documentation
```

## How It Works

The application uses a **producer-consumer threading pattern** for efficient audio processing:

1. **Recording Thread (Producer)**: A background thread continuously captures audio from your USB microphone at 16kHz and places 1280-sample chunks into a queue
2. **Processing Thread (Consumer)**: The main thread periodically reads from the queue and processes audio for wake word detection
3. **Sleep Between Predictions**: Configurable sleep interval prevents high CPU usage without interrupting audio capture
4. **Wake Word Detection**: OpenWakeWord analyzes audio chunks using neural networks (ONNX runtime)
5. **Threshold Check**: If confidence exceeds threshold, trigger action
6. **Video Playback**: Recording pauses, MPV plays the video in fullscreen mode
7. **Buffer Clearing**: Both hardware buffer and queue are cleared to prevent false triggers
8. **Resume Listening**: Recording thread restarts and listening continues

This architecture ensures:
- ✅ Continuous, uninterrupted audio recording
- ✅ Configurable CPU usage via prediction interval
- ✅ No audio loss during processing
- ✅ Clean separation of concerns

## Future Improvements

- [ ] Random video selection from folder
- [ ] Web interface for configuration
- [ ] Smart home integration (webhooks)
- [ ] Multiple action types (not just video)
- [ ] Voice commands after wake word (using Whisper STT)

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open source. Please check with your organization's policies.

## Acknowledgments

- [OpenWakeWord](https://github.com/dscripka/openWakeWord) - Wake word detection engine
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Audio I/O library
- [MPV](https://mpv.io/) - Media player

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Run `python test_microphone.py` to diagnose audio issues
3. Check OpenWakeWord documentation for model-specific issues
4. Review the application logs in the console output

---

**Happy wake word detecting! 🎤**


