"""Application constants and enums."""

from enum import Enum, auto


class CameraStatus(Enum):
    """Camera connection status."""
    OFFLINE = auto()
    CONNECTING = auto()
    ONLINE = auto()
    ERROR = auto()


class StreamQuality(Enum):
    """RTSP stream quality options."""
    MAIN = 0      # High quality, main stream
    SUB = 1       # Lower quality, sub stream (better for grid view)


# Dahua RTSP path templates
DAHUA_RTSP_PATH = "/cam/realmonitor?channel={channel}&subtype={subtype}"

# Default ports
DEFAULT_RTSP_PORT = 554
DEFAULT_HTTP_PORT = 80
DAHUA_PROPRIETARY_PORT = 37777

# Network scanning
CAMERA_SCAN_PORTS = [DAHUA_PROPRIETARY_PORT, DEFAULT_RTSP_PORT, DEFAULT_HTTP_PORT]
SCAN_TIMEOUT_SECONDS = 5

# UI defaults
DEFAULT_GRID_COLUMNS = 2
DEFAULT_WINDOW_SIZE = (1280, 720)

# Streaming
FRAME_BUFFER_SIZE = 2
RECONNECT_DELAY_SECONDS = 5
