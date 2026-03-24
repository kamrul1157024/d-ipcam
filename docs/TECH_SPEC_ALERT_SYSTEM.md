# D-IPCam AI Alert System - Technical Specification

## Overview

Add AI-powered video analysis to D-IPCam using SmolVLM2 models for real-time security monitoring and alerting. The system features a dedicated AI tab with rule-based alert configuration, reference image attachments, conditional logic, and multiple notification channels.

---

## Goals

1. **On-device AI** - No cloud dependency, privacy-first
2. **Visual Rule Builder** - Create complex alert conditions via UI
3. **Reference Images** - Attach images (faces, objects) for tracking
4. **Multi-Channel Alerts** - System notifications, sound, webhook, email
5. **Per-Camera Binding** - Assign AI rules to specific cameras
6. **Lazy Model Loading** - Download model only when first configured
7. **Customizable Prompts** - Full control over VLM prompts

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              D-IPCam Application                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           MAIN WINDOW                                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │ Cameras  │ │   Grid   │ │    AI    │ │  Alerts  │ │ Settings │      │   │
│  │  │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │      │   │
│  │  └──────────┘ └──────────┘ └────┬─────┘ └──────────┘ └──────────┘      │   │
│  └─────────────────────────────────┼───────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                            AI TAB                                        │   │
│  │  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │   │
│  │  │   Model Panel   │  │              Rules Panel                     │   │   │
│  │  │  - Model select │  │  ┌─────────────────────────────────────┐    │   │   │
│  │  │  - Download     │  │  │ Rule: "Track John at Front Door"    │    │   │   │
│  │  │  - Status       │  │  │ Camera: Front Door                  │    │   │   │
│  │  │                 │  │  │ Condition: Person matches [photo]   │    │   │   │
│  │  └─────────────────┘  │  │ Action: Notify + Webhook            │    │   │   │
│  │                        │  └─────────────────────────────────────┘    │   │   │
│  │  ┌─────────────────┐  │  ┌─────────────────────────────────────┐    │   │   │
│  │  │ Reference Panel │  │  │ Rule: "Detect Package Delivery"     │    │   │   │
│  │  │  - Face library │  │  │ Camera: Porch                       │    │   │   │
│  │  │  - Object refs  │  │  │ Condition: Package detected         │    │   │   │
│  │  │  - Upload       │  │  │ Action: System Notification         │    │   │   │
│  │  └─────────────────┘  │  └─────────────────────────────────────┘    │   │   │
│  │                        │  [+ Add New Rule]                           │   │   │
│  │                        └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          SERVICES LAYER                                  │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐    │   │
│  │  │VLMService │  │RuleEngine │  │AlertRouter│  │NotificationService│    │   │
│  │  │           │──▶│           │──▶│           │──▶│                   │    │   │
│  │  │ Inference │  │ Evaluate  │  │  Route    │  │ - System Notif    │    │   │
│  │  │           │  │ Conditions│  │  Alerts   │  │ - Sound           │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘  │ - Webhook         │    │   │
│  │                                                │ - Email           │    │   │
│  │                                                └───────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. AI Rules (Not just AlertConfig)

Instead of simple on/off toggles, users create **AI Rules** with:
- **Name** - Human-readable rule name
- **Camera Binding** - Which camera(s) this rule applies to
- **Condition** - What to detect (with optional reference images)
- **Action** - What to do when triggered (notification channels)
- **Schedule** - When the rule is active

### 2. Reference Library

Users can upload reference images for:
- **Faces** - "Alert when John arrives" (with John's photo)
- **Objects** - "Alert when my car is seen" (with car photo)
- **Scenes** - "Alert when garage door is open" (with reference of open door)

### 3. Conditional Logic

Rules support conditions like:
- Simple: "Person detected"
- Reference: "Person matches [uploaded face]"
- Compound: "Person detected AND time is after 10pm"
- Negation: "Motion detected AND NOT family member"

### 4. Alert Channels

Multiple ways to be notified:
- **System Notification** - macOS notification center
- **Sound** - Play alert sound
- **Webhook** - POST to URL (for Home Assistant, IFTTT, etc.)
- **Email** - Send email with snapshot (future)

---

## Data Models

### AIRule (replaces AlertConfig)

```python
@dataclass
class AIRule:
    id: int
    name: str
    enabled: bool = True

    # Camera binding
    camera_ids: list[int] = field(default_factory=list)  # Empty = all cameras

    # Condition (serialized as JSON)
    condition: RuleCondition = None

    # Custom prompt (optional - overrides auto-generated)
    custom_prompt: str = ""
    use_custom_prompt: bool = False

    # Analysis settings
    analysis_interval_seconds: int = 5
    confidence_threshold: float = 0.7
    cooldown_seconds: int = 60  # Min time between alerts for same rule

    # Actions
    actions: list[AlertAction] = field(default_factory=list)

    # Schedule
    schedule_enabled: bool = False
    schedule: RuleSchedule = None

    # Metadata
    created_at: datetime = None
    last_triggered: datetime = None
    trigger_count: int = 0
```

### RuleCondition (Condition Tree)

```python
@dataclass
class RuleCondition:
    """Base condition - can be simple or compound."""
    pass

@dataclass
class SimpleCondition(RuleCondition):
    """Single detection condition."""
    detection_type: str  # "person", "vehicle", "face", "object", "motion", "custom"
    reference_id: int = None  # Link to ReferenceImage if matching specific face/object
    custom_description: str = ""  # For "custom" type, user describes what to look for

@dataclass
class CompoundCondition(RuleCondition):
    """Combines multiple conditions with AND/OR/NOT."""
    operator: str  # "AND", "OR", "NOT"
    conditions: list[RuleCondition] = field(default_factory=list)

@dataclass
class TimeCondition(RuleCondition):
    """Time-based condition."""
    after_time: str = None  # "22:00"
    before_time: str = None  # "06:00"
    days_of_week: list[int] = None  # [0,1,2,3,4,5,6] = Mon-Sun
```

### ReferenceImage

```python
@dataclass
class ReferenceImage:
    id: int
    name: str
    category: str  # "face", "object", "scene"
    image_path: str  # Local file path
    description: str = ""  # User description for VLM context
    embedding: bytes = None  # Optional: pre-computed embedding for faster matching
    created_at: datetime = None
```

### AlertAction

```python
@dataclass
class AlertAction:
    type: str  # "system_notification", "sound", "webhook", "email"
    enabled: bool = True
    config: dict = field(default_factory=dict)
    # config examples:
    # system_notification: {"title_template": "{rule_name}", "body_template": "{description}"}
    # sound: {"sound_file": "alert.wav", "volume": 0.8}
    # webhook: {"url": "http://...", "method": "POST", "headers": {}, "body_template": "{}"}
    # email: {"to": "user@example.com", "subject_template": "...", "include_snapshot": true}
```

### AlertChannel (Global Config)

```python
@dataclass
class AlertChannel:
    id: int
    name: str
    type: str  # "system_notification", "sound", "webhook", "email"
    enabled: bool = True
    config: dict = field(default_factory=dict)
    # Reusable channel configurations
```

### RuleSchedule

```python
@dataclass
class RuleSchedule:
    """When the rule is active."""
    type: str  # "always", "time_range", "days_only"

    # For time_range
    start_time: str = "00:00"
    end_time: str = "23:59"

    # For days_only
    active_days: list[int] = field(default_factory=lambda: [0,1,2,3,4,5,6])

    # Quiet hours (inverse - when NOT to alert)
    quiet_hours_enabled: bool = False
    quiet_start: str = "22:00"
    quiet_end: str = "07:00"
```

### ModelConfig (unchanged)

```python
@dataclass
class ModelConfig:
    model_id: str = "SmolVLM2-500M"
    model_path: str = ""
    downloaded: bool = False
    download_progress: float = 0.0
    last_used: datetime = None
```

### AlertEvent (history - enhanced)

```python
@dataclass
class AlertEvent:
    id: int
    rule_id: int
    rule_name: str
    camera_id: int
    camera_name: str
    timestamp: datetime

    # Detection details
    detection_type: str
    description: str
    confidence: float
    matched_reference_id: int = None  # If matched a reference image

    # Evidence
    frame_path: str
    vlm_raw_response: str = ""

    # Actions taken
    actions_triggered: list[str] = field(default_factory=list)

    # Status
    acknowledged: bool = False
    false_positive: bool = False  # User feedback for learning
```

---

## Available Models

| Model ID | HuggingFace Model | Size | VRAM | Speed | Use Case |
|----------|-------------------|------|------|-------|----------|
| `SmolVLM2-256M` | `HuggingFaceTB/SmolVLM2-256M-Video-Instruct` | 256M | 1.4GB | Fast | Real-time, low-end |
| `SmolVLM2-500M` | `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` | 500M | 1.8GB | Balanced | **Default** |
| `SmolVLM2-2.2B` | `HuggingFaceTB/SmolVLM2-2.2B-Instruct` | 2.2B | 4GB | Accurate | Best quality |

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
    model_download_progress = pyqtSignal(str, float)  # model_id, progress
    model_ready = pyqtSignal(str)  # model_id
    model_error = pyqtSignal(str, str)  # model_id, error
    inference_complete = pyqtSignal(int, str, dict)  # camera_id, response, metadata

    def download_model(self, model_id: str) -> None:
        """Download model in background thread."""

    def load_model(self, model_id: str) -> bool:
        """Load model into memory."""

    def unload_model(self) -> None:
        """Free model from memory."""

    def analyze_frame(
        self,
        camera_id: int,
        frame: np.ndarray,
        prompt: str,
        reference_images: list[np.ndarray] = None
    ) -> None:
        """Analyze frame with optional reference images."""

    def is_model_ready(self) -> bool:
        """Check if model is loaded."""
```

### 2. RuleEngine

```python
class RuleEngine(QObject):
    """Evaluates AI rules against VLM responses."""

    alert_triggered = pyqtSignal(AlertEvent)

    def __init__(self, vlm_service: VLMService, rule_repo: AIRuleRepository):
        self._vlm = vlm_service
        self._rule_repo = rule_repo
        self._active_rules: dict[int, list[AIRule]] = {}  # camera_id -> rules
        self._cooldowns: dict[int, datetime] = {}  # rule_id -> last_triggered

    def start_monitoring(self, camera_id: int) -> None:
        """Start monitoring camera with assigned rules."""

    def stop_monitoring(self, camera_id: int) -> None:
        """Stop monitoring camera."""

    def process_frame(self, camera_id: int, frame: np.ndarray) -> None:
        """Process frame against all active rules for camera."""

    def build_prompt(self, rule: AIRule, reference_images: list[ReferenceImage]) -> str:
        """Build VLM prompt from rule condition."""

    def evaluate_response(self, rule: AIRule, vlm_response: str) -> tuple[bool, str, float]:
        """Evaluate VLM response against rule condition. Returns (triggered, description, confidence)."""

    def _check_schedule(self, rule: AIRule) -> bool:
        """Check if rule is active based on schedule."""

    def _check_cooldown(self, rule: AIRule) -> bool:
        """Check if rule is in cooldown period."""
```

### 3. AlertRouter

```python
class AlertRouter(QObject):
    """Routes alerts to configured channels."""

    def __init__(self, notification_service: NotificationService):
        self._notifier = notification_service
        self._channels: dict[int, AlertChannel] = {}

    def route_alert(self, event: AlertEvent, actions: list[AlertAction]) -> None:
        """Send alert through all configured actions."""

    def _send_system_notification(self, event: AlertEvent, config: dict) -> None:
        """Send macOS system notification."""

    def _play_sound(self, config: dict) -> None:
        """Play alert sound."""

    def _send_webhook(self, event: AlertEvent, config: dict) -> None:
        """Send webhook POST request."""

    def _send_email(self, event: AlertEvent, config: dict) -> None:
        """Send email with snapshot (future)."""
```

### 4. NotificationService

```python
class NotificationService:
    """macOS system notifications."""

    def send(self, title: str, body: str, image_path: str = None) -> None:
        """Send system notification."""

    def request_permission(self) -> bool:
        """Request notification permission."""

    def play_sound(self, sound_file: str, volume: float = 1.0) -> None:
        """Play alert sound."""
```

---

## UI Components

### 1. AI Tab (New Main Tab)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  D-IPCam                                              [Cameras] [Grid] [AI] [⚙️] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ 🤖 AI Model                      │  │ 📋 AI Rules                    [+ Add] │ │
│  │ ─────────────────────────────── │  │ ────────────────────────────────────── │ │
│  │                                  │  │                                        │ │
│  │ Model: [SmolVLM2-500M      ▼]   │  │ ┌────────────────────────────────────┐ │ │
│  │ Status: ● Ready (1.8GB)         │  │ │ ✓ Track Family Members              │ │ │
│  │         [Change Model]          │  │ │   📷 Front Door, Backyard           │ │ │
│  │                                  │  │ │   👤 Face matches: Mom, Dad, Kids   │ │ │
│  │ ─────────────────────────────── │  │ │   🔔 System Notification            │ │ │
│  │ 📷 Reference Library            │  │ │                    [Edit] [Delete]  │ │ │
│  │                                  │  │ └────────────────────────────────────┘ │ │
│  │ Faces (4)                       │  │                                        │ │
│  │ ┌────┐ ┌────┐ ┌────┐ ┌────┐    │  │ ┌────────────────────────────────────┐ │ │
│  │ │Mom │ │Dad │ │Kid1│ │Kid2│    │  │ │ ✓ Package Delivery Alert            │ │ │
│  │ └────┘ └────┘ └────┘ └────┘    │  │ │   📷 Porch Camera                   │ │ │
│  │ [+ Add Face]                    │  │ │   📦 Package detected               │ │ │
│  │                                  │  │ │   🔔 Notification + Webhook         │ │ │
│  │ Objects (2)                     │  │ │                    [Edit] [Delete]  │ │ │
│  │ ┌────┐ ┌────┐                   │  │ └────────────────────────────────────┘ │ │
│  │ │Car │ │Bike│                   │  │                                        │ │
│  │ └────┘ └────┘                   │  │ ┌────────────────────────────────────┐ │ │
│  │ [+ Add Object]                  │  │ │ ○ Night Intruder Detection          │ │ │
│  │                                  │  │ │   📷 All Cameras                    │ │ │
│  │ ─────────────────────────────── │  │ │   🚶 Person + Time after 11pm       │ │ │
│  │ 📢 Alert Channels               │  │ │   🚫 NOT matching family faces      │ │ │
│  │                                  │  │ │   🔔 Notification + Sound           │ │ │
│  │ ✓ System Notification           │  │ │                    [Edit] [Delete]  │ │ │
│  │ ✓ Alert Sound                   │  │ └────────────────────────────────────┘ │ │
│  │ ○ Webhook (not configured)     │  │                                        │ │
│  │ ○ Email (not configured)       │  │ ┌────────────────────────────────────┐ │ │
│  │ [Configure Channels]            │  │ │ ✓ Custom: Garage Door Open          │ │ │
│  │                                  │  │ │   📷 Garage Camera                  │ │ │
│  │                                  │  │ │   💬 "Alert if garage door open"    │ │ │
│  │                                  │  │ │   🔔 System Notification            │ │ │
│  │                                  │  │ │                    [Edit] [Delete]  │ │ │
│  │                                  │  │ └────────────────────────────────────┘ │ │
│  └─────────────────────────────────┘  └──────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Add/Edit Rule Dialog

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Create AI Rule                                                            [X]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Rule Name: [Track Family Members_________________________________]             │
│                                                                                  │
│  ═══ Camera Binding ════════════════════════════════════════════════════════   │
│  Apply to:  ○ All Cameras   ● Selected Cameras                                 │
│             [✓] Front Door  [✓] Backyard  [ ] Garage  [ ] Porch                │
│                                                                                  │
│  ═══ Detection Condition ═══════════════════════════════════════════════════   │
│                                                                                  │
│  ┌─ Condition Builder ─────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  [When ▼]  [Person ▼]  [matches ▼]  [Select Reference ▼]                │   │
│  │                                                                          │   │
│  │  Selected References:                                                    │   │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐                                           │   │
│  │  │Mom │ │Dad │ │Kid1│ │Kid2│  [+ Add]                                  │   │
│  │  └────┘ └────┘ └────┘ └────┘                                           │   │
│  │                                                                          │   │
│  │  [+ Add Another Condition]                                               │   │
│  │                                                                          │   │
│  │  ─── OR use Custom Prompt ───                                           │   │
│  │  [ ] Use custom prompt instead                                           │   │
│  │  [                                                                    ]  │   │
│  │  [                                                                    ]  │   │
│  │  [                                                                    ]  │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ═══ Alert Actions ═════════════════════════════════════════════════════════   │
│  When triggered, do:                                                            │
│  [✓] System Notification   [✓] Play Sound   [ ] Webhook   [ ] Email            │
│                                                                                  │
│  ═══ Settings ══════════════════════════════════════════════════════════════   │
│  Check every: [5 seconds ▼]   Confidence: [Medium (70%) ▼]                     │
│  Cooldown: [60 seconds ▼] (minimum time between alerts)                        │
│                                                                                  │
│  ═══ Schedule (Optional) ═══════════════════════════════════════════════════   │
│  [ ] Only active during specific times                                          │
│  Active: [00:00] to [23:59]   Days: [M][T][W][T][F][S][S]                       │
│                                                                                  │
│                                                    [Cancel]  [Save Rule]        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Condition Builder (Visual)

```
┌─ Condition Builder ─────────────────────────────────────────────────────────────┐
│                                                                                  │
│  ┌─ Condition Group (AND) ─────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  ┌─ Condition 1 ──────────────────────────────────────────────────┐     │   │
│  │  │ [Person ▼] [is detected ▼]                                      │     │   │
│  │  └─────────────────────────────────────────────────────── [✕]─────┘     │   │
│  │                                                                          │   │
│  │                              [AND ▼]                                     │   │
│  │                                                                          │   │
│  │  ┌─ Condition 2 ──────────────────────────────────────────────────┐     │   │
│  │  │ [Time ▼] [is after ▼] [22:00]                                   │     │   │
│  │  └─────────────────────────────────────────────────────── [✕]─────┘     │   │
│  │                                                                          │   │
│  │                              [AND ▼]                                     │   │
│  │                                                                          │   │
│  │  ┌─ Condition 3 (NOT) ────────────────────────────────────────────┐     │   │
│  │  │ [NOT ▼] [Face ▼] [matches ▼] [Family Faces ▼]                   │     │   │
│  │  └─────────────────────────────────────────────────────── [✕]─────┘     │   │
│  │                                                                          │   │
│  │  [+ Add Condition]                                                       │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  Preview (auto-generated prompt):                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ "Analyze this camera frame. Alert if: A person is detected AND the      │   │
│  │  current time is after 10pm AND the person does NOT match any of the    │   │
│  │  reference faces provided. Reference faces: [4 images attached]"        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Reference Image Upload Dialog

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Add Reference Image                                                       [X]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Category: ● Face   ○ Object   ○ Scene                                         │
│                                                                                  │
│  ┌─────────────────────────────────────┐                                        │
│  │                                     │                                        │
│  │                                     │                                        │
│  │       [Drag & Drop Image Here]      │                                        │
│  │              or                      │                                        │
│  │         [Browse Files]              │                                        │
│  │                                     │                                        │
│  │                                     │                                        │
│  └─────────────────────────────────────┘                                        │
│                                                                                  │
│  Name: [Mom_________________________________________________]                   │
│                                                                                  │
│  Description (helps AI identify):                                               │
│  [Adult woman with brown hair, glasses_________________________]               │
│  [____________________________________________________________]               │
│                                                                                  │
│                                                    [Cancel]  [Add Reference]    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5. Alert Channels Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Alert Channels                                                            [X]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ═══ System Notification ══════════════════════════════════════════════════    │
│  [✓] Enabled                                                                    │
│  Title: [{rule_name}_______________________________________________]           │
│  Body:  [{description} at {camera_name}____________________________]           │
│  [ ] Include snapshot image                                                     │
│                                                                                  │
│  ═══ Alert Sound ══════════════════════════════════════════════════════════    │
│  [✓] Enabled                                                                    │
│  Sound: [Default Alert ▼]  [▶ Test]                                            │
│  Volume: [████████░░] 80%                                                       │
│                                                                                  │
│  ═══ Webhook ══════════════════════════════════════════════════════════════    │
│  [ ] Enabled                                                                    │
│  URL: [https://your-server.com/webhook_____________________________]           │
│  Method: [POST ▼]                                                               │
│  Headers: [{"Authorization": "Bearer xxx"}__________________________]          │
│  Body Template:                                                                 │
│  [{"event": "{alert_type}", "camera": "{camera_name}", "time": "{timestamp}"}] │
│  [▶ Test Webhook]                                                               │
│                                                                                  │
│  ═══ Email (Coming Soon) ══════════════════════════════════════════════════    │
│  [ ] Enabled (requires SMTP configuration)                                      │
│                                                                                  │
│                                                              [Cancel]  [Save]   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6. Alerts History Tab

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  D-IPCam                                    [Cameras] [Grid] [AI] [Alerts] [⚙️]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Filter: [All Rules ▼] [All Cameras ▼] [Last 24 hours ▼]    [🔍 Search]  [Clear]│
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │ 12:45 PM │ 🚶 Track Family Members          │ Front Door    │ High (92%)  │ │
│  │ Today    │ "Mom detected at front door"    │               │ [👁️] [✓] [✕]│ │
│  ├───────────────────────────────────────────────────────────────────────────┤ │
│  │ 11:30 AM │ 📦 Package Delivery Alert        │ Porch         │ High (88%)  │ │
│  │ Today    │ "Package left at door"           │               │ [👁️] [✓] [✕]│ │
│  ├───────────────────────────────────────────────────────────────────────────┤ │
│  │ 10:15 AM │ 🚗 Vehicle Detection             │ Driveway      │ Med (75%)   │ │
│  │ Today    │ "White sedan in driveway"        │               │ [👁️] [✓] [✕]│ │
│  ├───────────────────────────────────────────────────────────────────────────┤ │
│  │ Yesterday│ ⚠️ Night Intruder Detection      │ Backyard      │ High (85%)  │ │
│  │ 11:45 PM │ "Unknown person near fence"      │               │ [👁️] [✓] [✕]│ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [👁️] = View Snapshot   [✓] = Mark as Valid   [✕] = Mark as False Positive      │
│                                                                                  │
│  Stats: 23 alerts today │ 4 false positives │ 156 alerts this week              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Prompt Generation

### Auto-Generated Prompt from Conditions

```python
class PromptBuilder:
    """Builds VLM prompts from rule conditions."""

    SYSTEM_PROMPT = """You are a security camera AI. Analyze this camera frame.
Your task: {task_description}

{reference_context}

Response format:
DETECTED: <yes/no> | <description> | <confidence: low/medium/high>

Be concise. One sentence description max."""

    def build_prompt(self, rule: AIRule, references: list[ReferenceImage]) -> str:
        """Build complete prompt from rule."""
        task = self._describe_condition(rule.condition)
        ref_context = self._build_reference_context(references)

        return self.SYSTEM_PROMPT.format(
            task_description=task,
            reference_context=ref_context
        )

    def _describe_condition(self, condition: RuleCondition) -> str:
        """Convert condition tree to natural language."""
        if isinstance(condition, SimpleCondition):
            return self._describe_simple(condition)
        elif isinstance(condition, CompoundCondition):
            return self._describe_compound(condition)
        elif isinstance(condition, TimeCondition):
            return self._describe_time(condition)

    def _describe_simple(self, c: SimpleCondition) -> str:
        if c.detection_type == "person":
            if c.reference_id:
                return "Detect if a person matches the provided reference face"
            return "Detect if any person is visible"
        elif c.detection_type == "vehicle":
            return "Detect if any vehicle is visible"
        elif c.detection_type == "custom":
            return c.custom_description
        # ... etc

    def _build_reference_context(self, refs: list[ReferenceImage]) -> str:
        if not refs:
            return ""

        context = "Reference images provided:\n"
        for i, ref in enumerate(refs, 1):
            context += f"- Image {i}: {ref.name}"
            if ref.description:
                context += f" ({ref.description})"
            context += "\n"
        return context
```

### Example Generated Prompts

**Simple: Person Detection**
```
You are a security camera AI. Analyze this camera frame.
Your task: Detect if any person is visible

Response format:
DETECTED: <yes/no> | <description> | <confidence: low/medium/high>
```

**With Reference: Face Matching**
```
You are a security camera AI. Analyze this camera frame.
Your task: Detect if a person matches any of the provided reference faces

Reference images provided:
- Image 1: Mom (Adult woman with brown hair, glasses)
- Image 2: Dad (Adult man, beard, tall)
- Image 3: Kid1 (Teenage boy, blonde hair)

Response format:
DETECTED: <yes/no> | <description> | <confidence: low/medium/high>
```

**Complex: Night Intruder**
```
You are a security camera AI. Analyze this camera frame.
Your task: Detect if a person is visible AND they do NOT match any of the family reference faces

Reference images provided:
- Image 1: Mom (Adult woman with brown hair)
- Image 2: Dad (Adult man, beard)
- Image 3: Kid1 (Teenage boy)
- Image 4: Kid2 (Young girl)

Response format:
DETECTED: <yes/no> | <description> | <confidence: low/medium/high>
```

**Custom Prompt Override**
```
(User's exact custom prompt is used instead)
```

---

## Database Schema

### ai_rules table

```sql
CREATE TABLE ai_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    camera_ids TEXT DEFAULT '[]',  -- JSON array
    condition TEXT DEFAULT '{}',   -- JSON serialized RuleCondition
    custom_prompt TEXT DEFAULT '',
    use_custom_prompt INTEGER DEFAULT 0,
    analysis_interval_seconds INTEGER DEFAULT 5,
    confidence_threshold REAL DEFAULT 0.7,
    cooldown_seconds INTEGER DEFAULT 60,
    actions TEXT DEFAULT '[]',     -- JSON array of AlertAction
    schedule_enabled INTEGER DEFAULT 0,
    schedule TEXT DEFAULT '{}',    -- JSON serialized RuleSchedule
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0
);
```

### reference_images table

```sql
CREATE TABLE reference_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'face', 'object', 'scene'
    image_path TEXT NOT NULL,
    description TEXT DEFAULT '',
    embedding BLOB,  -- Optional pre-computed embedding
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### alert_channels table

```sql
CREATE TABLE alert_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'system_notification', 'sound', 'webhook', 'email'
    enabled INTEGER DEFAULT 1,
    config TEXT DEFAULT '{}'  -- JSON
);
```

### alert_history table

```sql
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER,
    rule_name TEXT,
    camera_id INTEGER,
    camera_name TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detection_type TEXT,
    description TEXT,
    confidence REAL,
    matched_reference_id INTEGER,
    frame_path TEXT,
    vlm_raw_response TEXT,
    actions_triggered TEXT DEFAULT '[]',  -- JSON array
    acknowledged INTEGER DEFAULT 0,
    false_positive INTEGER DEFAULT 0,
    FOREIGN KEY (rule_id) REFERENCES ai_rules(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id),
    FOREIGN KEY (matched_reference_id) REFERENCES reference_images(id)
);
```

### model_config table (unchanged)

```sql
CREATE TABLE model_config (
    id INTEGER PRIMARY KEY DEFAULT 1,
    model_id TEXT DEFAULT 'SmolVLM2-500M',
    model_path TEXT DEFAULT '',
    downloaded INTEGER DEFAULT 0,
    last_used TIMESTAMP
);
```

---

## File Structure

```
d_ipcam/
├── data/
│   ├── models/
│   │   ├── ai_rule.py           # AIRule, RuleCondition, etc.
│   │   ├── reference_image.py   # ReferenceImage
│   │   ├── alert_channel.py     # AlertChannel, AlertAction
│   │   ├── alert_event.py       # AlertEvent
│   │   └── model_config.py      # ModelConfig
│   └── repositories/
│       ├── ai_rule_repo.py
│       ├── reference_image_repo.py
│       ├── alert_channel_repo.py
│       ├── alert_history_repo.py
│       └── model_config_repo.py
├── services/
│   ├── vlm_service.py           # SmolVLM2 model management
│   ├── rule_engine.py           # Rule evaluation
│   ├── alert_router.py          # Route alerts to channels
│   ├── notification_service.py  # macOS notifications, sounds
│   └── prompt_builder.py        # Generate prompts from rules
└── ui/
    ├── tabs/
    │   ├── ai_tab.py            # Main AI configuration tab
    │   └── alerts_tab.py        # Alert history tab
    └── widgets/
        ├── dialogs/
        │   ├── rule_editor_dialog.py
        │   ├── reference_upload_dialog.py
        │   ├── channel_config_dialog.py
        │   └── model_download_dialog.py
        ├── condition_builder.py  # Visual condition builder
        ├── reference_library.py  # Reference image grid
        └── alert_history_list.py
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Data models (AIRule, RuleCondition, ReferenceImage, etc.)
- [ ] Database tables and repositories
- [ ] VLMService (model download, loading, inference)
- [ ] PromptBuilder (generate prompts from conditions)

### Phase 2: Rule Engine
- [ ] RuleEngine (evaluate rules, manage cooldowns)
- [ ] AlertRouter (route to channels)
- [ ] NotificationService (system notifications, sounds)
- [ ] Webhook support

### Phase 3: UI - AI Tab
- [ ] AI Tab layout (model panel, rules list, reference library)
- [ ] Model download dialog
- [ ] Reference image upload dialog
- [ ] Alert channels configuration

### Phase 4: UI - Rule Editor
- [ ] Rule editor dialog
- [ ] Condition builder (visual AND/OR/NOT)
- [ ] Reference image picker
- [ ] Custom prompt editor
- [ ] Schedule configuration

### Phase 5: UI - Alerts Tab
- [ ] Alert history list with filters
- [ ] Snapshot viewer
- [ ] Mark as false positive
- [ ] Statistics

### Phase 6: Integration & Polish
- [ ] Connect StreamService to RuleEngine
- [ ] Camera binding in CameraView
- [ ] Performance optimization
- [ ] Error handling
- [ ] Update DMG build

---

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing deps ...
    "mlx-vlm>=0.1.0",                           # SmolVLM2 on Apple Silicon
    "huggingface-hub>=0.20",                    # Model download
    "pyobjc-framework-UserNotifications>=10.0", # macOS notifications
    "httpx>=0.27",                              # Async HTTP for webhooks
]
```

---

## Acceptance Criteria

1. **Dedicated AI Tab** - Separate tab for all AI configuration
2. **Visual Rule Builder** - Create rules with conditions without writing code
3. **Reference Images** - Upload faces/objects for matching
4. **Compound Conditions** - AND/OR/NOT logic for complex rules
5. **Custom Prompts** - Option to write custom VLM prompts
6. **Camera Binding** - Assign rules to specific cameras
7. **Multiple Alert Channels** - Notification, sound, webhook
8. **Alert History** - View past alerts with snapshots
9. **False Positive Feedback** - Mark alerts for potential learning
10. **Model Selection** - Choose between 256M, 500M, 2.2B models
11. **Lazy Download** - Model downloads only when needed

---

## Open Questions

1. Should we support importing/exporting rules?
2. Add rule templates (pre-built rules for common scenarios)?
3. Support for scheduled rule activation/deactivation?
4. Integration with Home Assistant via webhook discovery?
5. Support for multiple reference images per face (better matching)?

---

*Last Updated: 2026-03-24*
*Author: Claude Code*
