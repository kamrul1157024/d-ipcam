# D-IPCam - Technical Architecture

## Overview

D-IPCam follows a **layered architecture** pattern with strict separation of concerns between UI, Services, and Data layers. This design enables:

- **Testability** - Each layer can be tested independently
- **Maintainability** - Changes in one layer don't cascade to others
- **ML-Ready** - Services layer designed for future ML pipeline integration
- **Flexibility** - Swap implementations (e.g., SQLite → PostgreSQL) without UI changes

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│                           (PyQt6 UI)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ MainWindow  │  │   Dialogs   │  │       Widgets           │  │
│  │             │  │  - Add/Edit │  │  - CameraView           │  │
│  │             │  │  - Settings │  │  - CameraGrid           │  │
│  │             │  │             │  │  - CameraList           │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                              │                                   │
│                              │  ViewModels / Signals             │
├──────────────────────────────┼───────────────────────────────────┤
│                              ▼                                   │
│                        SERVICE LAYER                             │
│                    (Business Logic)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ DiscoveryService│  │  StreamService  │  │  CameraService  │  │
│  │                 │  │                 │  │                 │  │
│  │ - scan_network()│  │ - start_stream()│  │ - add_camera()  │  │
│  │ - find_cameras()│  │ - stop_stream() │  │ - get_cameras() │  │
│  │                 │  │ - get_frame()   │  │ - update_camera()│ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                     │           │
│           │    ┌───────────────┴───────────────┐    │           │
│           │    │      ML Pipeline (Future)      │    │           │
│           │    │  - ObjectDetectionService      │    │           │
│           │    │  - FaceRecognitionService      │    │           │
│           │    └───────────────────────────────┘    │           │
│           │                                          │           │
├───────────┼──────────────────────────────────────────┼───────────┤
│           ▼                                          ▼           │
│                          DATA LAYER                              │
│              (Persistence & External I/O)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Repositories  │  │     Models      │  │   External I/O  │  │
│  │                 │  │                 │  │                 │  │
│  │ - CameraRepo    │  │ - Camera        │  │ - RTSPClient    │  │
│  │ - SettingsRepo  │  │ - Settings      │  │ - NetworkScanner│  │
│  │ - EventRepo     │  │ - Event         │  │                 │  │
│  └────────┬────────┘  └─────────────────┘  └─────────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │     SQLite      │                                            │
│  │   (cameras.db)  │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

### 1. Presentation Layer (UI)

**Location:** `d_ipcam/ui/`

**Responsibility:** Display data and capture user interactions. **No business logic.**

| Component | Purpose |
|-----------|---------|
| `MainWindow` | Application shell, layout management |
| `CameraView` | Single camera stream display widget |
| `CameraGrid` | Multi-camera grid layout |
| `CameraList` | Sidebar with camera list |
| `Dialogs` | Add/Edit camera, Settings dialogs |

**Rules:**
- UI components receive data via **signals/slots** or **ViewModels**
- UI calls service methods but never accesses data layer directly
- UI does not contain business logic (validation, calculations)
- Widgets are reusable and stateless where possible

### 2. Service Layer (Business Logic)

**Location:** `d_ipcam/services/`

**Responsibility:** Orchestrate business operations, enforce rules, coordinate between UI and Data.

| Service | Purpose |
|---------|---------|
| `CameraService` | CRUD operations for cameras, validation |
| `DiscoveryService` | Network scanning, camera detection |
| `StreamService` | RTSP stream management, frame delivery |
| `MLService` (future) | ML inference pipeline |

**Rules:**
- Services are stateless (or manage minimal state)
- Services use repositories for persistence
- Services emit signals for async operations
- Services handle all business validation

### 3. Data Layer (Persistence & I/O)

**Location:** `d_ipcam/data/`

**Responsibility:** Data persistence, external I/O, data models.

| Component | Purpose |
|-----------|---------|
| `models/` | Data classes (Camera, Settings, Event) |
| `repositories/` | Database operations (CameraRepository) |
| `database.py` | SQLite connection management |

**Rules:**
- Models are pure data containers (dataclasses)
- Repositories handle all SQL operations
- No business logic in data layer
- Repositories return models, not raw data

---

## Project Structure

```
~/d-ipcam/
├── docs/
│   ├── ARCHITECTURE.md          # This document
│   └── API.md                   # Service API documentation
│
├── d_ipcam/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── app.py                   # QApplication setup
│   │
│   ├── core/                    # Shared utilities
│   │   ├── __init__.py
│   │   ├── config.py            # App configuration
│   │   ├── signals.py           # Custom Qt signals
│   │   └── constants.py         # App constants
│   │
│   ├── data/                    # DATA LAYER
│   │   ├── __init__.py
│   │   ├── database.py          # SQLite connection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── camera.py        # Camera dataclass
│   │   │   └── settings.py      # Settings dataclass
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── base.py          # Base repository
│   │       └── camera_repo.py   # Camera repository
│   │
│   ├── services/                # SERVICE LAYER
│   │   ├── __init__.py
│   │   ├── camera_service.py    # Camera CRUD
│   │   ├── discovery_service.py # Network scanning
│   │   └── stream_service.py    # RTSP streaming
│   │
│   └── ui/                      # PRESENTATION LAYER
│       ├── __init__.py
│       ├── main_window.py       # Main application window
│       ├── styles.py            # QSS styles
│       └── widgets/
│           ├── __init__.py
│           ├── camera_view.py   # Single camera widget
│           ├── camera_grid.py   # Grid layout widget
│           ├── camera_list.py   # Camera list sidebar
│           └── dialogs/
│               ├── __init__.py
│               ├── add_camera.py
│               └── settings.py
│
├── tests/
│   ├── __init__.py
│   ├── test_services/
│   ├── test_data/
│   └── test_ui/
│
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Data Flow Examples

### Example 1: Adding a Camera

```
┌─────────┐    ┌──────────────┐    ┌───────────────┐    ┌────────────┐
│   UI    │    │   Service    │    │  Repository   │    │  Database  │
│ Dialog  │    │CameraService │    │  CameraRepo   │    │   SQLite   │
└────┬────┘    └──────┬───────┘    └───────┬───────┘    └──────┬─────┘
     │                │                     │                   │
     │ add_camera()   │                     │                   │
     │ (name,ip,cred) │                     │                   │
     ├───────────────►│                     │                   │
     │                │ validate()          │                   │
     │                │ create Camera model │                   │
     │                │                     │                   │
     │                │ save(camera)        │                   │
     │                ├────────────────────►│                   │
     │                │                     │ INSERT INTO...    │
     │                │                     ├──────────────────►│
     │                │                     │                   │
     │                │                     │◄──────────────────┤
     │                │◄────────────────────┤ return camera.id  │
     │                │                     │                   │
     │ emit signal    │                     │                   │
     │ camera_added   │                     │                   │
     │◄───────────────┤                     │                   │
     │                │                     │                   │
     │ update list    │                     │                   │
     │                │                     │                   │
```

### Example 2: Displaying Camera Stream

```
┌───────────┐    ┌──────────────┐    ┌────────────┐
│    UI     │    │   Service    │    │   OpenCV   │
│CameraView │    │StreamService │    │ VideoCapture│
└─────┬─────┘    └──────┬───────┘    └──────┬─────┘
      │                 │                    │
      │ start_stream()  │                    │
      │ (camera)        │                    │
      ├────────────────►│                    │
      │                 │ build RTSP URL     │
      │                 │ cv2.VideoCapture() │
      │                 ├───────────────────►│
      │                 │                    │
      │                 │◄───────────────────┤
      │                 │  (stream handle)   │
      │                 │                    │
      │                 │ start frame thread │
      │                 │                    │
      │   ┌─────────────┴──────────┐        │
      │   │  Frame Loop (Thread)   │        │
      │   │  while running:        │        │
      │   │    frame = read()      │───────►│
      │   │    emit frame_ready    │◄───────┤
      │   └────────────────────────┘        │
      │                 │                    │
      │ frame_ready     │                    │
      │ signal          │                    │
      │◄────────────────┤                    │
      │                 │                    │
      │ update QLabel   │                    │
      │ (QImage)        │                    │
```

---

## Communication Patterns

### Signals & Slots (PyQt6)

Services emit signals for async events. UI connects to these signals.

```python
# In StreamService
class StreamService(QObject):
    frame_ready = pyqtSignal(int, np.ndarray)  # camera_id, frame
    stream_error = pyqtSignal(int, str)        # camera_id, error_msg

# In CameraView widget
def __init__(self, camera_id: int, stream_service: StreamService):
    stream_service.frame_ready.connect(self._on_frame)
    stream_service.stream_error.connect(self._on_error)
```

### Dependency Injection

Services and repositories are injected, not instantiated directly.

```python
# In main.py
def main():
    # Data layer
    db = Database("cameras.db")
    camera_repo = CameraRepository(db)

    # Service layer
    camera_service = CameraService(camera_repo)
    discovery_service = DiscoveryService()
    stream_service = StreamService()

    # UI layer (receives services)
    window = MainWindow(
        camera_service=camera_service,
        discovery_service=discovery_service,
        stream_service=stream_service
    )
```

---

## Future ML Integration

The architecture supports ML pipeline integration at the service layer:

```
StreamService ──► MLPipelineService ──► UI
     │                   │
     │ raw frames        │ annotated frames
     │                   │ + detections
     ▼                   ▼
  ┌─────────────────────────────────────┐
  │         MLPipelineService           │
  │  ┌─────────────┐ ┌───────────────┐  │
  │  │ObjectDetect │ │FaceRecognition│  │
  │  │  (YOLO)     │ │   (future)    │  │
  │  └─────────────┘ └───────────────┘  │
  └─────────────────────────────────────┘
```

The `MLPipelineService` will:
1. Receive frames from `StreamService`
2. Run inference (YOLO, face recognition, etc.)
3. Return annotated frames + detection metadata
4. Emit signals for alerts/events

---

## Configuration

**Location:** `d_ipcam/core/config.py`

```python
@dataclass
class AppConfig:
    # Database
    db_path: str = "~/.d_ipcam/cameras.db"

    # Network scanning
    scan_ports: list[int] = (37777, 554, 80)
    scan_timeout: int = 5  # seconds

    # Streaming
    default_rtsp_port: int = 554
    frame_buffer_size: int = 2
    reconnect_delay: int = 5  # seconds

    # UI
    grid_columns: int = 2
    default_window_size: tuple[int, int] = (1280, 720)
```

---

## Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| **Data** | Raise specific exceptions (`CameraNotFoundError`, `DatabaseError`) |
| **Service** | Catch data exceptions, emit error signals, log errors |
| **UI** | Display user-friendly error messages, never crash |

---

## Testing Strategy

| Layer | Test Type | Tools |
|-------|-----------|-------|
| **Data** | Unit tests | pytest, in-memory SQLite |
| **Service** | Unit + Integration | pytest, mocks for I/O |
| **UI** | Widget tests | pytest-qt |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2024-XX-XX | Initial architecture |
