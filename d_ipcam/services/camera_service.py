"""Camera service for business logic."""

from PyQt6.QtCore import QObject, pyqtSignal

from d_ipcam.data.models import Camera
from d_ipcam.data.repositories import CameraRepository


class CameraService(QObject):
    """Service for camera management operations."""

    # Signals
    camera_added = pyqtSignal(Camera)
    camera_updated = pyqtSignal(Camera)
    camera_deleted = pyqtSignal(int)  # camera_id

    def __init__(self, repository: CameraRepository) -> None:
        """Initialize camera service.

        Args:
            repository: Camera repository for data access
        """
        super().__init__()
        self.repo = repository

    def get_all_cameras(self) -> list[Camera]:
        """Get all cameras.

        Returns:
            List of all cameras
        """
        return self.repo.get_all()

    def get_enabled_cameras(self) -> list[Camera]:
        """Get all enabled cameras.

        Returns:
            List of enabled cameras
        """
        return self.repo.get_enabled()

    def get_camera(self, camera_id: int) -> Camera:
        """Get a camera by ID.

        Args:
            camera_id: Camera ID

        Returns:
            Camera instance
        """
        return self.repo.get_by_id(camera_id)

    def add_camera(
        self,
        name: str,
        ip: str,
        username: str = "admin",
        password: str = "",
        port: int = 554,
        channel: int = 1,
    ) -> Camera:
        """Add a new camera.

        Args:
            name: Display name for the camera
            ip: IP address
            username: Camera username
            password: Camera password
            port: RTSP port
            channel: Camera channel number

        Returns:
            Created camera
        """
        camera = Camera(
            name=name,
            ip=ip,
            username=username,
            password=password,
            port=port,
            channel=channel,
        )

        saved = self.repo.save(camera)
        self.camera_added.emit(saved)
        return saved

    def update_camera(self, camera: Camera) -> Camera:
        """Update an existing camera.

        Args:
            camera: Camera with updated fields

        Returns:
            Updated camera
        """
        saved = self.repo.save(camera)
        self.camera_updated.emit(saved)
        return saved

    def delete_camera(self, camera_id: int) -> None:
        """Delete a camera.

        Args:
            camera_id: Camera ID to delete
        """
        self.repo.delete(camera_id)
        self.camera_deleted.emit(camera_id)

    def camera_exists(self, ip: str) -> bool:
        """Check if a camera with the given IP exists.

        Args:
            ip: IP address to check

        Returns:
            True if camera exists
        """
        return self.repo.get_by_ip(ip) is not None
