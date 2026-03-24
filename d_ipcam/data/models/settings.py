"""Settings model."""

from dataclasses import dataclass


@dataclass
class AppSettings:
    """Application settings."""

    default_username: str = "admin"
    default_password: str = ""
    default_rtsp_port: int = 554
    grid_columns: int = 2

    def has_default_credentials(self) -> bool:
        """Check if default credentials are set.

        Returns:
            True if both username and password are set
        """
        return bool(self.default_username and self.default_password)
