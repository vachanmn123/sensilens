# SensiLens - Real-Time Object Detection and Depth Awareness System

SensiLens is an assistive technology system designed to help visually impaired individuals navigate their environment safely. The system uses real-time object detection and depth estimation to detect approaching objects and provide audio feedback through text-to-speech alerts and distance-based beep warnings.

## Features

- **Real-time Object Detection**: Uses YOLOv8 for fast and accurate object detection
- **Depth Estimation**: Employs Depth Anything V2 model for metric depth prediction
- **Approaching Object Detection**: Calculates object velocity to identify objects moving toward the user
- **Audio Feedback System**: 
  - Text-to-speech announcements for identified objects
  - Distance-based beeping with spatial audio (panning based on object position)
  - Adjustable beep frequency based on approach speed
- **Distributed Architecture**: 
  - Laptop/desktop for heavy processing (object detection & depth estimation)
  - Raspberry Pi for audio playback and camera streaming
- **Live Video Feed**: Real-time visualization with bounding boxes, depth, and speed information

## System Architecture

The system consists of two main components:

1. **Processing Unit (Laptop/Desktop)**: 
   - Receives RTSP video stream from Raspberry Pi
   - Performs object detection using YOLOv8
   - Calculates depth maps using Depth Anything V2
   - Tracks objects and computes approach velocity
   - Sends audio commands to Raspberry Pi via HTTP API

2. **Raspberry Pi Unit**:
   - Captures video using camera and streams via MediaMTX (RTSP)
   - Runs Flask server to receive audio playback commands
   - Handles text-to-speech and distance beeps locally

## Prerequisites

### On Laptop/Desktop
- Python 3.8+
- CUDA-capable GPU (recommended) or Apple Silicon for MPS acceleration
- UV package manager (recommended) or pip

### On Raspberry Pi
- Raspberry Pi 4 or newer
- Camera module or USB camera
- Speaker or audio output device
- Flask and dependencies

## Installation

### Laptop/Desktop Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd final-year-proj
   ```

2. **Install dependencies**:
   ```bash
   # Using UV (recommended)
   uv pip install -r requirements.txt
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Download model checkpoints**:
   
   The project requires the following model files in the `checkpoints/` directory:
   - YOLOv8 model: `yolov8n.pt` (downloads automatically on first run)
   - Depth Anything V2 models:
     - `depth_anything_v2_metric_hypersim_vits.pth`
     - `depth_anything_v2_metric_hypersim_vitl.pth`
   - Piper TTS voice models:
     - `en_US-lessac-low.onnx` and `en_US-lessac-low.onnx.json`
     - `en_US-lessac-high.onnx` and `en_US-lessac-high.onnx.json`
     - Other voice variants as needed

4. **Configure Raspberry Pi IP address**:
   
   Edit `main.py` and update line 37 with your Raspberry Pi's IP address or hostname:
   ```python
   def reader_thread(rtsp_url="rtsp://YOUR_RPI_IP:8554/rpicam"):
   ```

### Raspberry Pi Setup

1. **Install dependencies**:
   ```bash
   pip install flask piper-tts sounddevice soundfile numpy
   ```

2. **Copy necessary files to Raspberry Pi**:
   ```bash
   scp pi_server.py tts.py pi@raspberrypi.local:~/sensilens/
   scp -r checkpoints/en_US-lessac-low.onnx* pi@raspberrypi.local:~/sensilens/checkpoints/
   ```

3. **Install and configure MediaMTX**:
   
   a. Download MediaMTX:
   ```bash
   wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_*_linux_arm64v8.tar.gz
   tar -xzf mediamtx_*_linux_arm64v8.tar.gz
   sudo mv mediamtx /usr/local/bin/
   ```
   
   b. Create MediaMTX configuration:
   ```bash
   sudo mkdir -p /etc/mediamtx
   sudo nano /etc/mediamtx/mediamtx.yml
   ```
   
   c. Add the following configuration to allow RTSP streaming with the path `rpicam`:
   ```yaml
   paths:
     rpicam:
       source: publisher
       runOnInit: rpicam-vid -t 0 --width 1280 --height 720 --framerate 30 -o - | ffmpeg -f h264 -i - -c:v copy -f rtsp rtsp://localhost:$RTSP_PORT/$MTX_PATH
       runOnInitRestart: yes
   ```
   
   d. Create systemd service for auto-start:
   ```bash
   sudo nano /etc/systemd/system/mediamtx.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=MediaMTX RTSP Server
   After=network.target
   
   [Service]
   Type=simple
   User=pi
   ExecStart=/usr/local/bin/mediamtx /etc/mediamtx/mediamtx.yml
   Restart=always
   RestartSec=5
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   e. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mediamtx
   sudo systemctl start mediamtx
   ```

4. **Set up auto-start for Flask server** (optional):
   
   Create systemd service:
   ```bash
   sudo nano /etc/systemd/system/sensilens.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=SensiLens Audio Server
   After=network.target mediamtx.service
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/sensilens
   ExecStart=/usr/bin/python3 pi_server.py
   Restart=always
   RestartSec=5
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable sensilens
   sudo systemctl start sensilens
   ```

## Usage

### Running the System

1. **On Raspberry Pi**:
   
   Start the Flask server (if not running as systemd service):
   ```bash
   cd ~/sensilens
   python3 pi_server.py
   ```
   
   The server will start on port 5000.

2. **On Laptop/Desktop**:
   
   a. Ensure the Raspberry Pi IP is correctly configured in `main.py`
   
   b. Run the main application:
   ```bash
   uv run main.py
   # or
   python main.py
   ```
   
   c. The system will:
   - Connect to the Raspberry Pi's RTSP stream
   - Start detecting objects in real-time
   - Display a live feed window with bounding boxes and information
   - Send audio alerts to the Raspberry Pi when objects approach

3. **Exit the application**:
   
   Press `q` in the video window or `Ctrl+C` in the terminal.

## How It Works

1. **Video Capture**: The Raspberry Pi camera captures video and streams it via MediaMTX RTSP server
2. **Frame Processing**: The laptop receives frames and processes them through:
   - YOLOv8 for object detection and tracking
   - Depth Anything V2 for metric depth estimation
3. **Motion Analysis**: The system calculates approach velocity by comparing depth changes over time
4. **Alert Generation**: When an object is approaching (speed > 0.5 m/s):
   - TTS alert: "object_name approaching"
   - Distance beeps with spatial audio (panning based on position)
5. **Audio Playback**: The Raspberry Pi receives HTTP requests and plays audio locally

## Configuration

### Adjusting Detection Sensitivity

In `main.py`, modify:
```python
# Line ~105: Confidence threshold
if conf < 0.5:  # Lower = more detections, higher = fewer false positives
    continue

# Line ~124: Approach speed threshold
if speed > 0.5:  # Lower = more sensitive to approaching objects
    play_distance_beep(speed, x_dist)
    play_tts(f"{name} approaching")
```

### Changing Depth Model

In `depth_calc.py`:
```python
encoder = "vits"  # Options: 'vits' (fastest), 'vitb', 'vitl' (most accurate)
dataset = "hypersim"  # 'hypersim' for indoor, 'vkitti' for outdoor
max_depth = 20  # 20 for indoor, 80 for outdoor
```

### TTS Voice Selection

In `tts.py` or `o_tts.py`:
```python
voice = PiperVoice.load("checkpoints/en_US-lessac-low.onnx")
# Available options: lessac-low/high, kristin-medium, hfc_female-medium
```

## Performance Tips

- Use GPU acceleration when available (CUDA or MPS)
- Lower resolution improves FPS: Modify `cv2.resize(frame, (640, 480))` in `main.py`
- Use `vits` encoder for faster depth estimation (less accurate)
- Reduce confidence threshold for fewer detections to process
- Use wired Ethernet connection between laptop and Raspberry Pi for lower latency

## Troubleshooting

### Cannot connect to RTSP stream
- Verify Raspberry Pi IP address in `main.py`
- Check MediaMTX is running: `sudo systemctl status mediamtx`
- Test RTSP stream: `ffplay rtsp://raspberrypi.local:8554/rpicam`

### No audio output on Raspberry Pi
- Check Flask server is running: `curl http://raspberrypi.local:5000/tts -X POST -H "Content-Type: application/json" -d '{"text":"test"}'`
- Verify audio device: `aplay -l`
- Check volume: `alsamixer`

### Low FPS
- Use GPU acceleration (CUDA/MPS)
- Switch to `vits` encoder for depth estimation
- Reduce video resolution
- Use wired network connection

### High false positive detections
- Increase confidence threshold (line ~105 in `main.py`)
- Use larger YOLOv8 model (e.g., `yolov8l.pt` instead of `yolov8n.pt`)

## Project Structure

```
final-year-proj/
├── main.py                 # Main application (laptop)
├── pi_server.py           # Flask server for audio (Raspberry Pi)
├── obj_detection.py       # YOLOv8 object detection
├── depth_calc.py          # Depth Anything V2 depth estimation
├── tts.py                 # TTS and audio for Raspberry Pi
├── o_tts.py               # Alternative TTS implementation
├── requirements.txt       # Python dependencies
├── checkpoints/           # Model files
│   ├── yolov8n.pt
│   ├── depth_anything_v2_*.pth
│   └── en_US-*.onnx
├── depth_anything_v2/     # Depth model implementation
└── sounds/
    └── generated/         # Cached TTS audio files
```

## Dependencies

### Laptop/Desktop
- OpenCV (video processing)
- PyTorch (deep learning)
- Ultralytics (YOLOv8)
- NumPy (numerical operations)
- Piper TTS (text-to-speech)
- PyDub/SimpleAudio/SoundDevice (audio playback)

### Raspberry Pi
- Flask (HTTP server)
- Piper TTS (text-to-speech)
- SoundDevice/SoundFile (audio playback)
- NumPy (audio processing)


## Acknowledgments

- [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) for depth estimation
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for object detection
- [Piper TTS](https://github.com/rhasspy/piper) for text-to-speech
- [MediaMTX](https://github.com/bluenviron/mediamtx) for RTSP streaming

## Contributors

1. Vachan MN - [vachanmn.tech](https://vachanmn.tech)
2. Kusikumar B - [LinkedIn](https://www.linkedin.com/in/kushi-kumar-b-39b320259)
3. Mallikarjun HS - [LinkedIn](https://www.linkedin.com/in/mallikarjuna-h-s-8762232a3)
4. Pavan Kumar VM
