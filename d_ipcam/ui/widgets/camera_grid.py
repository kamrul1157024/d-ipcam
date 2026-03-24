"""Camera grid widget for displaying multiple cameras."""

import numpy as np
from typing import Dict

from PyQt6.QtCore import pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QWidget, QGridLayout

from d_ipcam.core.constants import CameraStatus
from d_ipcam.data.models import Camera
from d_ipcam.services import StreamService, AudioService, TalkbackService
from d_ipcam.services.audio_service import TalkMode
from .camera_view import CameraView


class CameraGrid(QWidget):
    """Grid widget for displaying multiple camera streams."""

    # Forward audio signals from views
    listen_toggled = pyqtSignal(int, bool)  # camera_id, enabled
    talk_started = pyqtSignal(int)  # camera_id
    talk_stopped = pyqtSignal(int)  # camera_id

    def __init__(
        self,
        stream_service: StreamService,
        audio_service: AudioService,
        talkback_service: TalkbackService,
        columns: int = 2,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize camera grid.

        Args:
            stream_service: Service for managing streams
            audio_service: Service for audio playback/capture
            talkback_service: Service for sending audio to cameras
            columns: Number of columns in the grid
            parent: Parent widget
        """
        super().__init__(parent)
        self.stream_service = stream_service
        self.audio_service = audio_service
        self.talkback_service = talkback_service
        self.columns = columns

        self._views: Dict[int, CameraView] = {}  # camera_id -> CameraView
        self._cameras: Dict[int, Camera] = {}  # camera_id -> Camera

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(8)

    def _connect_signals(self) -> None:
        """Connect service signals."""
        self.stream_service.frame_ready.connect(self._on_frame_ready)
        self.stream_service.audio_ready.connect(self._on_audio_ready)
        self.stream_service.status_changed.connect(self._on_status_changed)
        self.stream_service.error_occurred.connect(self._on_error)

        # Connect mic data to talkback service
        self.audio_service.mic_data_ready.connect(self._on_mic_data)

    def add_camera(self, camera: Camera) -> None:
        """Add a camera to the grid.

        Args:
            camera: Camera to add
        """
        if camera.id is None:
            return

        if camera.id in self._views:
            return

        # Create view
        view = CameraView(camera)

        # Connect view audio signals
        view.listen_toggled.connect(self._on_listen_toggled)
        view.talk_started.connect(self._on_talk_started)
        view.talk_stopped.connect(self._on_talk_stopped)

        self._views[camera.id] = view
        self._cameras[camera.id] = camera

        # Set up audio player for this camera
        self.audio_service.setup_player(camera.id)

        # Add to grid layout
        self._relayout()

        # Start streaming
        self.stream_service.start_stream(camera)

    def remove_camera(self, camera_id: int) -> None:
        """Remove a camera from the grid.

        Args:
            camera_id: Camera ID to remove
        """
        if camera_id not in self._views:
            return

        # Stop stream and audio
        self.stream_service.stop_stream(camera_id)
        self.audio_service.stop_player(camera_id)

        # Remove view
        view = self._views.pop(camera_id)
        self._cameras.pop(camera_id, None)
        self.layout.removeWidget(view)
        view.deleteLater()

        # Relayout
        self._relayout()

    def clear(self) -> None:
        """Remove all cameras from the grid."""
        self.stream_service.stop_all_streams()
        self.audio_service.stop_all()
        self.talkback_service.stop_all()

        for view in self._views.values():
            self.layout.removeWidget(view)
            view.deleteLater()

        self._views.clear()
        self._cameras.clear()

    def set_cameras(self, cameras: list[Camera]) -> None:
        """Set the cameras to display.

        Args:
            cameras: List of cameras to display
        """
        # Stop all existing streams
        self.clear()

        # Add new cameras
        for camera in cameras:
            if camera.enabled:
                self.add_camera(camera)

    def _relayout(self) -> None:
        """Relayout camera views in the grid."""
        # Remove all from layout (but keep widgets)
        for i in reversed(range(self.layout.count())):
            self.layout.takeAt(i)

        # Add back in grid order
        camera_ids = sorted(self._views.keys())
        for i, camera_id in enumerate(camera_ids):
            row = i // self.columns
            col = i % self.columns
            self.layout.addWidget(self._views[camera_id], row, col)

    def set_columns(self, columns: int) -> None:
        """Set the number of grid columns.

        Args:
            columns: Number of columns
        """
        self.columns = max(1, columns)
        self._relayout()

    @pyqtSlot(int, np.ndarray)
    def _on_frame_ready(self, camera_id: int, frame: np.ndarray) -> None:
        """Handle new frame from stream.

        Args:
            camera_id: Camera ID
            frame: OpenCV frame
        """
        if camera_id in self._views:
            self._views[camera_id].update_frame(frame)

    @pyqtSlot(int, bytes, int, int)
    def _on_audio_ready(
        self,
        camera_id: int,
        audio_data: bytes,
        sample_rate: int,
        channels: int
    ) -> None:
        """Handle audio data from stream.

        Args:
            camera_id: Camera ID
            audio_data: Raw PCM audio bytes
            sample_rate: Audio sample rate
            channels: Number of channels
        """
        # Play audio through audio service
        self.audio_service.play_audio(camera_id, audio_data)

    @pyqtSlot(int, CameraStatus)
    def _on_status_changed(self, camera_id: int, status: CameraStatus) -> None:
        """Handle camera status change.

        Args:
            camera_id: Camera ID
            status: New status
        """
        if camera_id in self._views:
            self._views[camera_id].set_status(status)

    @pyqtSlot(int, str)
    def _on_error(self, camera_id: int, error: str) -> None:
        """Handle stream error.

        Args:
            camera_id: Camera ID
            error: Error message
        """
        if camera_id in self._views:
            self._views[camera_id].set_status(CameraStatus.ERROR)

    @pyqtSlot(int, bool)
    def _on_listen_toggled(self, camera_id: int, enabled: bool) -> None:
        """Handle listen toggle from camera view.

        Args:
            camera_id: Camera ID
            enabled: True if listening enabled
        """
        self.audio_service.set_listen_enabled(camera_id, enabled)
        self.listen_toggled.emit(camera_id, enabled)

    @pyqtSlot(int)
    def _on_talk_started(self, camera_id: int) -> None:
        """Handle talk started from camera view.

        Args:
            camera_id: Camera ID
        """
        # Start mic capture
        self.audio_service.start_talk(camera_id)

        # Start talkback to camera
        if camera_id in self._cameras:
            self.talkback_service.start_talkback(self._cameras[camera_id])

        self.talk_started.emit(camera_id)

    @pyqtSlot(int)
    def _on_talk_stopped(self, camera_id: int) -> None:
        """Handle talk stopped from camera view.

        Args:
            camera_id: Camera ID
        """
        # Stop mic capture
        self.audio_service.stop_talk()

        # Stop talkback to camera
        self.talkback_service.stop_talkback(camera_id)

        self.talk_stopped.emit(camera_id)

    @pyqtSlot(int, bytes)
    def _on_mic_data(self, camera_id: int, audio_data: bytes) -> None:
        """Handle microphone data from audio service.

        Args:
            camera_id: Target camera ID
            audio_data: PCM audio bytes
        """
        # Forward to talkback service
        self.talkback_service.send_audio(camera_id, audio_data)
