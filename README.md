# D-IPCam

A macOS desktop application for viewing and managing RTSP IP cameras.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green)
![macOS](https://img.shields.io/badge/macOS-10.15+-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Camera Discovery** - Scan your local network to find IP cameras
- **RTSP Streaming** - View live video feeds from multiple cameras
- **Multi-Camera Grid** - Display 1x1, 2x2, 3x3, or 4x4 camera layouts
- **Audio Playback** - Listen to camera audio streams
- **Two-Way Audio** - Push-to-talk and toggle talk modes
- **Quality Selection** - Switch between Main and Sub streams
- **Dark Theme** - Modern dark UI design
- **Camera Persistence** - SQLite database stores camera configurations

## Installation

### From DMG (Recommended)

1. Download `D-IPCam.dmg` from [Releases](https://github.com/kamrul1157024/d-ipcam/releases)
2. Open the DMG file
3. Drag D-IPCam to Applications folder
4. Launch from Applications

### From Source

```bash
# Clone the repository
git clone https://github.com/kamrul1157024/d-ipcam.git
cd d-ipcam

# Install dependencies (requires uv)
make setup

# Run the application
make run
```

## Requirements

- macOS 10.15 (Catalina) or later
- Apple Silicon or Intel Mac
- Python 3.12+ (for development)

## Usage

### Adding Cameras

1. Click **"+ Add"** to manually add a camera
2. Or click **"Scan"** to discover cameras on your network
3. Enter camera credentials (username/password)
4. Select stream quality (Sub stream recommended for multiple cameras)

### Viewing Cameras

- Click on a camera in the sidebar to add it to the grid
- Use the **Grid** dropdown to change layout (1x1 to 4x4)
- Right-click a camera in the list to Edit or Delete

### Audio Controls

Each camera view has audio controls:
- **Listen** (speaker icon) - Toggle camera audio playback
- **Talk** (microphone icon) - Push-to-talk or toggle mode
  - Right-click for mode selection

## Development

```bash
# Install dependencies
make setup

# Run in development mode
make run-dev

# Build macOS app
make build

# Build DMG installer
make dmg

# Run linter
make lint

# Format code
make format

# Clean build artifacts
make clean
```

## Project Structure

```
d-ipcam/
├── d_ipcam/
│   ├── core/           # Configuration and constants
│   ├── data/           # Database and models
│   │   ├── models/     # Data models (Camera, Settings)
│   │   └── repositories/  # Database access
│   ├── services/       # Business logic
│   │   ├── audio_service.py
│   │   ├── camera_service.py
│   │   ├── discovery_service.py
│   │   ├── stream_service.py
│   │   └── talkback_service.py
│   └── ui/             # User interface
│       ├── main_window.py
│       └── widgets/    # UI components
├── scripts/            # Build scripts
├── docs/               # Documentation
└── Makefile
```

## Tech Stack

- **Python 3.12** - Programming language
- **PyQt6** - GUI framework
- **PyAV** - RTSP streaming (FFmpeg wrapper)
- **OpenCV** - Video processing
- **SQLite** - Camera persistence
- **PyInstaller** - macOS app bundling

## Camera Compatibility

Works with any IP camera that supports RTSP streaming:
- Generic RTSP cameras
- ONVIF-compatible cameras
- Dahua, Hikvision, Reolink, etc.

Common RTSP URL formats:
- Generic: `rtsp://user:pass@ip:554/stream`
- Dahua: `rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0`
- Hikvision: `rtsp://user:pass@ip:554/Streaming/Channels/101`

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
