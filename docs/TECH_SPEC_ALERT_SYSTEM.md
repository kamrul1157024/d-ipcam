# D-IPCam AI Alert System - Technical Specification

## Overview

Add AI-powered video analysis to D-IPCam using SmolVLM2 models for real-time security monitoring and alerting. The system analyzes camera frames periodically and triggers macOS system notifications when configurable events are detected.

---

## Goals

1. **On-device AI** - No cloud dependency, privacy-first
2. **User-configurable** - Alert types, frequency, model selection via UI
3. **Opt-in monitoring** - Explicitly enabled per camera
4. **Lazy model loading** - Download model only when first configured
5. **Low resource usage** - Efficient frame sampling, MLX optimization for Apple Silicon

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           D-IPCam Application                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐│
│  │    UI Layer  │     │   Services   │     │       Data Layer         ││
│  ├──────────────┤     ├──────────────┤     ├──────────────────────────┤│
│  │              │     │              │     │                          ││
│  │ AlertConfig  │◄───►│ AlertService │◄───►│ AlertConfigRepository    ││
│  │   Dialog     │     │              │     │                          ││
│  │              │     │      │       │     │ AlertHistoryRepository   ││
│  │ AlertHistory │     │      ▼       │     │                          ││
│  │   Widget     │     │ ┌──────────┐ │     │ Models:                  ││
│  │              │     │ │VLMService│ │     │  - AlertConfig           ││
│  │ CameraView   │     │ │(SmolVLM2)│ │     │  - AlertEvent            ││
│  │ + AI Toggle  │     │ └──────────┘ │     │  - ModelConfig           ││
│  │              │     │      │       │     │                          ││
│  └──────────────┘     │      ▼       │     └──────────────────────────┘│
│                       │ ┌──────────┐ │                                 │
│                       │ │Notifier  │ │                                 │
│                       │ │ Service  │ │──────► macOS Notifications      │
│                       │ └──────────┘ │                                 │
│                       └──────────────┘                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Models

### AlertConfig (per camera)

```python
@dataclass
class AlertConfig:
    camera_id: int
    enabled: bool = False

    # Alert types (user configurable)
    detect_person: bool = True
    detect_vehicle: bool = True
    detect_animal: bool = False
    detect_package: bool = False
    detect_motion: bool = True
    detect_anomaly: bool = True

    # Custom alert (user-defined prompt)
    custom_alert_enabled: bool = False
    custom_alert_prompt: str = ""

    # Analysis settings
    analysis_interval_seconds: int = 5  # 2, 5, 10 seconds
    confidence_threshold: float = 0.7   # 0.5, 0.7, 0.9

    # Quiet hours (no alerts)
    quiet_hours_enabled: bool = False
    quiet_start: str = "22:00"
    quiet_end: str = "07:00"
```

### ModelConfig (global)

```python
@dataclass
class ModelConfig:
    model_id: str = "SmolVLM2-500M"  # User selected
    model_path: str = ""             # Local path after download
    downloaded: bool = False
    download_progress: float = 0.0
    last_used: datetime = None
```

### AlertEvent (history)

```python
@dataclass
class AlertEvent:
    id: int
    camera_id: int
    camera_name: str
    timestamp: datetime
    alert_type: str          # "person", "vehicle", "motion", etc.
    description: str         # VLM response
    confidence: float
    frame_path: str          # Saved snapshot
    acknowledged: bool = False
```

---

## Available Models

| Model ID | HuggingFace Model | Size | VRAM | Speed | Use Case |
|----------|-------------------|------|------|-------|----------|
| `SmolVLM2-256M` | `HuggingFaceTB/SmolVLM2-256M-Video-Instruct` | 256M | 1.4GB | Fast | Low-end, real-time |
| `SmolVLM2-500M` | `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` | 500M | 1.8GB | Balanced | **Default** |
| `SmolVLM2-2.2B` | `HuggingFaceTB/SmolVLM2-2.2B-Instruct` | 2.2B | 4GB | Accurate | High accuracy |

MLX variants for Apple Silicon:
- `mlx-community/SmolVLM2-256M-Video-Instruct-mlx`
- `mlx-community/SmolVLM2-500M-Video-Instruct-mlx`
- `mlx-community/SmolVLM2-2.2B-Instruct-mlx`

---

## Services

### 1. VLMService (Vision Language Model)

```python
class VLMService(QObject):
    """Manages SmolVLM2 model loading and inference."""

    # Signals
    model_download_progress = pyqtSignal(float)  # 0.0 - 1.0
    model_ready = pyqtSignal()
    model_error = pyqtSignal(str)
    analysis_complete = pyqtSignal(int, str, float)  # camera_id, result, confidence

    def __init__(self):
        self.model = None
        self.processor = None
        self.model_config: ModelConfig = None
        self._inference_thread: QThread = None

    # --- Model Management ---

    def download_model(self, model_id: str) -> None:
        """Download model in background thread."""
        pass

    def load_model(self) -> bool:
        """Load model into memory (MLX for Mac, CUDA/CPU otherwise)."""
        pass

    def unload_model(self) -> None:
        """Free model from memory."""
        pass

    def is_model_ready(self) -> bool:
        """Check if model is loaded and ready."""
        pass

    # --- Inference ---

    def analyze_frame(
        self,
        camera_id: int,
        frame: np.ndarray,
        alert_config: AlertConfig
    ) -> None:
        """Analyze frame in background, emit analysis_complete signal."""
        pass

    def _build_prompt(self, config: AlertConfig) -> str:
        """Build analysis prompt based on alert config."""
        pass
```

### 2. AlertService

```python
class AlertService(QObject):
    """Coordinates frame sampling, VLM analysis, and notifications."""

    # Signals
    alert_triggered = pyqtSignal(AlertEvent)

    def __init__(
        self,
        vlm_service: VLMService,
        notifier_service: NotifierService,
        alert_repo: AlertConfigRepository,
        history_repo: AlertHistoryRepository,
    ):
        self._vlm = vlm_service
        self._notifier = notifier_service
        self._alert_repo = alert_repo
        self._history_repo = history_repo
        self._camera_timers: dict[int, QTimer] = {}
        self._last_frames: dict[int, np.ndarray] = {}

    # --- Monitoring Control ---

    def start_monitoring(self, camera_id: int) -> None:
        """Start AI monitoring for camera."""
        pass

    def stop_monitoring(self, camera_id: int) -> None:
        """Stop AI monitoring for camera."""
        pass

    def is_monitoring(self, camera_id: int) -> bool:
        """Check if camera is being monitored."""
        pass

    # --- Frame Handling ---

    def update_frame(self, camera_id: int, frame: np.ndarray) -> None:
        """Called by StreamService with latest frame."""
        pass

    def _on_analysis_timer(self, camera_id: int) -> None:
        """Timer callback - send frame to VLM."""
        pass

    # --- Alert Processing ---

    def _on_analysis_complete(
        self, camera_id: int, result: str, confidence: float
    ) -> None:
        """Handle VLM result, trigger alert if needed."""
        pass

    def _parse_vlm_response(self, response: str) -> tuple[str, str, float]:
        """Parse VLM response into (alert_type, description, confidence)."""
        pass
```

### 3. NotifierService

```python
class NotifierService:
    """Send macOS system notifications."""

    def send_alert(self, event: AlertEvent) -> None:
        """Send system notification for alert."""
        # Uses PyObjC for native macOS notifications
        pass

    def request_permission(self) -> bool:
        """Request notification permission from user."""
        pass
```

---

## UI Components

### 1. Alert Settings Dialog

**Location:** `d_ipcam/ui/widgets/dialogs/alert_settings_dialog.py`

```
┌─────────────────────────────────────────────────────────┐
│  AI Monitoring Settings - [Camera Name]           [X]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [✓] Enable AI Monitoring                               │
│                                                         │
│  ─── Model ───────────────────────────────────────────  │
│  Model: [SmolVLM2-500M (Recommended)     ▼]            │
│  Status: ● Downloaded (1.8GB)  [Redownload]            │
│                                                         │
│  ─── Detection Types ─────────────────────────────────  │
│  [✓] Person detected                                    │
│  [✓] Vehicle detected                                   │
│  [ ] Animal detected                                    │
│  [ ] Package/delivery detected                          │
│  [✓] Unusual motion                                     │
│  [✓] Anomaly/suspicious activity                        │
│                                                         │
│  ─── Custom Alert ────────────────────────────────────  │
│  [ ] Enable custom detection                            │
│  Prompt: [____________________________________]         │
│  Example: "Alert if garage door is open"               │
│                                                         │
│  ─── Settings ────────────────────────────────────────  │
│  Analysis frequency: [Every 5 seconds    ▼]            │
│  Confidence threshold: [Medium (0.7)     ▼]            │
│                                                         │
│  ─── Quiet Hours ─────────────────────────────────────  │
│  [ ] Enable quiet hours (no alerts)                     │
│  From: [22:00] To: [07:00]                             │
│                                                         │
│                              [Cancel]  [Save Settings]  │
└─────────────────────────────────────────────────────────┘
```

### 2. CameraView AI Toggle

Add to existing CameraView widget:

```
┌─────────────────────────────────────────┐
│  Camera Name                    [⚙️][X] │
├─────────────────────────────────────────┤
│                                         │
│                                         │
│           [Camera Feed]                 │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│  🔊  🎤  │  [🤖 AI: ON]  │  ⚙️ Settings │
└─────────────────────────────────────────┘
            ▲
            └── AI monitoring toggle + status
```

### 3. Alert History Widget (Sidebar or Dialog)

```
┌───────────────────────────────────────────┐
│  Alert History                    [Clear] │
├───────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐  │
│  │ 🚶 Person Detected                  │  │
│  │ Front Door - 2 min ago              │  │
│  │ "Person approaching front door"     │  │
│  │ [View Snapshot] [Dismiss]           │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │ 🚗 Vehicle Detected                 │  │
│  │ Driveway - 15 min ago               │  │
│  │ "Car parked in driveway"            │  │
│  │ [View Snapshot] [Dismiss]           │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │ ⚠️ Motion Detected                  │  │
│  │ Backyard - 1 hour ago               │  │
│  │ "Movement near fence"               │  │
│  │ [View Snapshot] [Dismiss]           │  │
│  └─────────────────────────────────────┘  │
└───────────────────────────────────────────┘
```

### 4. Model Download Dialog

```
┌─────────────────────────────────────────────┐
│  Download AI Model                          │
├─────────────────────────────────────────────┤
│                                             │
│  SmolVLM2-500M-Video-Instruct              │
│  Size: 1.8 GB                               │
│                                             │
│  ████████████░░░░░░░░░░░░  45%             │
│  Downloading: 810 MB / 1.8 GB               │
│  Speed: 25 MB/s                             │
│                                             │
│  This model will be stored locally and      │
│  used for AI-powered camera monitoring.     │
│                                             │
│                              [Cancel]       │
└─────────────────────────────────────────────┘
```

---

## Database Schema

### alert_config table

```sql
CREATE TABLE alert_config (
    camera_id INTEGER PRIMARY KEY,
    enabled INTEGER DEFAULT 0,
    detect_person INTEGER DEFAULT 1,
    detect_vehicle INTEGER DEFAULT 1,
    detect_animal INTEGER DEFAULT 0,
    detect_package INTEGER DEFAULT 0,
    detect_motion INTEGER DEFAULT 1,
    detect_anomaly INTEGER DEFAULT 1,
    custom_alert_enabled INTEGER DEFAULT 0,
    custom_alert_prompt TEXT DEFAULT '',
    analysis_interval_seconds INTEGER DEFAULT 5,
    confidence_threshold REAL DEFAULT 0.7,
    quiet_hours_enabled INTEGER DEFAULT 0,
    quiet_start TEXT DEFAULT '22:00',
    quiet_end TEXT DEFAULT '07:00',
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
);
```

### model_config table

```sql
CREATE TABLE model_config (
    id INTEGER PRIMARY KEY DEFAULT 1,
    model_id TEXT DEFAULT 'SmolVLM2-500M',
    model_path TEXT DEFAULT '',
    downloaded INTEGER DEFAULT 0,
    last_used TIMESTAMP
);
```

### alert_history table

```sql
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER,
    camera_name TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alert_type TEXT,
    description TEXT,
    confidence REAL,
    frame_path TEXT,
    acknowledged INTEGER DEFAULT 0,
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
);
```

---

## VLM Prompt Templates

### Security Analysis Prompt

```python
SECURITY_PROMPT_TEMPLATE = """You are a security camera AI assistant. Analyze this camera frame.

Active detection types:
{detection_types}

Rules:
1. Only report if you detect something from the active detection types above
2. Be concise - one sentence description maximum
3. Report confidence level (low/medium/high)

Response format (use exactly this format):
ALERT: <type> | <description> | <confidence>

OR if nothing detected:
NORMAL: No activity detected

Examples:
ALERT: person | Adult male walking toward front door | high
ALERT: vehicle | White sedan parking in driveway | high
ALERT: motion | Movement detected near window | medium
NORMAL: No activity detected
"""

def build_prompt(config: AlertConfig) -> str:
    detection_types = []
    if config.detect_person:
        detection_types.append("- PERSON: Any human presence")
    if config.detect_vehicle:
        detection_types.append("- VEHICLE: Cars, trucks, motorcycles")
    if config.detect_animal:
        detection_types.append("- ANIMAL: Dogs, cats, wildlife")
    if config.detect_package:
        detection_types.append("- PACKAGE: Boxes, deliveries left at door")
    if config.detect_motion:
        detection_types.append("- MOTION: Any significant movement")
    if config.detect_anomaly:
        detection_types.append("- ANOMALY: Unusual or suspicious activity")
    if config.custom_alert_enabled and config.custom_alert_prompt:
        detection_types.append(f"- CUSTOM: {config.custom_alert_prompt}")

    return SECURITY_PROMPT_TEMPLATE.format(
        detection_types="\n".join(detection_types)
    )
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Add `mlx-vlm` dependency to pyproject.toml
- [ ] Create data models (AlertConfig, ModelConfig, AlertEvent)
- [ ] Create database tables and repositories
- [ ] Implement VLMService (model download, loading, inference)
- [ ] Implement NotifierService (macOS notifications)

### Phase 2: Alert Service
- [ ] Implement AlertService (frame sampling, coordination)
- [ ] Add prompt templates
- [ ] Parse VLM responses
- [ ] Save alert history with snapshots

### Phase 3: UI Components
- [ ] Create AlertSettingsDialog
- [ ] Create ModelDownloadDialog
- [ ] Add AI toggle to CameraView
- [ ] Create AlertHistoryWidget
- [ ] Add menu/toolbar access to alert history

### Phase 4: Integration
- [ ] Connect StreamService to AlertService
- [ ] Wire up all UI signals/slots
- [ ] Add to main.py initialization
- [ ] Test end-to-end flow

### Phase 5: Polish
- [ ] Error handling and recovery
- [ ] Performance optimization
- [ ] Memory management (unload model when not needed)
- [ ] Quiet hours implementation
- [ ] Update DMG build with new dependencies

---

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing deps ...
    "mlx-vlm>=0.1.0",        # SmolVLM2 on Apple Silicon
    "huggingface-hub>=0.20", # Model download
    "pyobjc-framework-UserNotifications>=10.0",  # macOS notifications
]
```

---

## File Structure

```
d_ipcam/
├── data/
│   ├── models/
│   │   ├── alert_config.py      # AlertConfig dataclass
│   │   ├── alert_event.py       # AlertEvent dataclass
│   │   └── model_config.py      # ModelConfig dataclass
│   └── repositories/
│       ├── alert_config_repo.py
│       ├── alert_history_repo.py
│       └── model_config_repo.py
├── services/
│   ├── vlm_service.py           # SmolVLM2 model management
│   ├── alert_service.py         # Frame analysis coordination
│   └── notifier_service.py      # macOS notifications
└── ui/
    └── widgets/
        ├── dialogs/
        │   ├── alert_settings_dialog.py
        │   └── model_download_dialog.py
        ├── alert_history_widget.py
        └── camera_view.py       # Add AI toggle
```

---

## Acceptance Criteria

1. **Model Selection** - User can choose between 256M, 500M, 2.2B models
2. **Lazy Download** - Model downloads only when user enables AI monitoring
3. **Progress UI** - Download progress shown with cancel option
4. **Per-Camera Config** - Each camera has independent alert settings
5. **Alert Types** - User can toggle detection types (person, vehicle, etc.)
6. **Custom Alerts** - User can add custom detection prompt
7. **System Notifications** - Alerts trigger macOS notifications
8. **Alert History** - View past alerts with snapshots
9. **Quiet Hours** - Suppress alerts during configurable hours
10. **Memory Efficient** - Model unloaded when no cameras being monitored

---

## Security Considerations

1. **Local Processing** - All inference on-device, no cloud
2. **Snapshot Storage** - Alert snapshots stored in `~/.d_ipcam/alerts/`
3. **Retention Policy** - Auto-delete snapshots older than 30 days
4. **No Logging** - VLM responses not logged externally

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Model load time | < 10 seconds |
| Inference latency (500M) | < 2 seconds per frame |
| Memory usage (500M) | < 2GB |
| CPU impact during monitoring | < 20% |

---

## Open Questions

1. Should alert snapshots include bounding boxes?
2. Should we support multiple cameras monitoring simultaneously?
3. Add audio alerts in addition to system notifications?
4. Export alert history to CSV?

---

*Last Updated: 2026-03-24*
*Author: Claude Code*
