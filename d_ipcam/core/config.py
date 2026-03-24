"""Application configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from .constants import (
    CAMERA_SCAN_PORTS,
    DEFAULT_GRID_COLUMNS,
    DEFAULT_RTSP_PORT,
    DEFAULT_WINDOW_SIZE,
    FRAME_BUFFER_SIZE,
    RECONNECT_DELAY_SECONDS,
    SCAN_TIMEOUT_SECONDS,
)


@dataclass
class AppConfig:
    """Application configuration settings."""

    # Database
    db_path: Path = field(default_factory=lambda: Path.home() / ".d_ipcam" / "cameras.db")

    # Network scanning
    scan_ports: list[int] = field(default_factory=lambda: list(CAMERA_SCAN_PORTS))
    scan_timeout: int = SCAN_TIMEOUT_SECONDS

    # Streaming
    default_rtsp_port: int = DEFAULT_RTSP_PORT
    frame_buffer_size: int = FRAME_BUFFER_SIZE
    reconnect_delay: int = RECONNECT_DELAY_SECONDS

    # UI
    grid_columns: int = DEFAULT_GRID_COLUMNS
    window_size: tuple[int, int] = DEFAULT_WINDOW_SIZE

    def __post_init__(self) -> None:
        """Ensure config directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


# Global config instance
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the global application config."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def set_config(config: AppConfig) -> None:
    """Set the global application config."""
    global _config
    _config = config
