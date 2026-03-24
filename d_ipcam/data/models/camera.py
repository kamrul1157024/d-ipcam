"""Camera model."""

from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote

from d_ipcam.core.constants import DAHUA_RTSP_PATH, DEFAULT_RTSP_PORT, StreamQuality


@dataclass
class Camera:
    """Represents an IP camera."""

    name: str
    ip: str
    username: str = "admin"
    password: str = ""
    port: int = DEFAULT_RTSP_PORT
    channel: int = 1
    subtype: int = 1  # 0=Main, 1=Sub (default)
    enabled: bool = True
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_rtsp_url(self) -> str:
        """Build the full RTSP URL for this camera.

        Returns:
            Full RTSP URL with credentials
        """
        path = DAHUA_RTSP_PATH.format(channel=self.channel, subtype=self.subtype)

        if self.username and self.password:
            # URL-encode credentials to handle special characters
            encoded_user = quote(self.username, safe='')
            encoded_pass = quote(self.password, safe='')
            return f"rtsp://{encoded_user}:{encoded_pass}@{self.ip}:{self.port}{path}"
        else:
            return f"rtsp://{self.ip}:{self.port}{path}"

    def get_talkback_url(self) -> str:
        """Build the RTSP URL for talk-back audio to camera.

        Dahua cameras use: /cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif

        Returns:
            RTSP URL for sending audio to camera
        """
        path = f"/cam/realmonitor?channel={self.channel}&subtype=0&unicast=true&proto=Onvif"

        if self.username and self.password:
            encoded_user = quote(self.username, safe='')
            encoded_pass = quote(self.password, safe='')
            return f"rtsp://{encoded_user}:{encoded_pass}@{self.ip}:{self.port}{path}"
        else:
            return f"rtsp://{self.ip}:{self.port}{path}"

    def __str__(self) -> str:
        return f"Camera({self.name}, {self.ip})"
