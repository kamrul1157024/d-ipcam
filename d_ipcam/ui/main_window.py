"""Main application window."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QToolBar,
    QComboBox,
    QLabel,
    QMessageBox,
)
from PyQt6.QtGui import QAction

from d_ipcam import __version__
from d_ipcam.data.models import Camera
from d_ipcam.services import CameraService, DiscoveryService, StreamService, AudioService, TalkbackService, UpdateService, ReleaseInfo
from d_ipcam.services.discovery_service import DiscoveredCamera
from .widgets import (
    CameraGrid,
    CameraListWidget,
    AddCameraDialog,
    DiscoveryDialog,
    UpdateDialog,
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        camera_service: CameraService,
        discovery_service: DiscoveryService,
        stream_service: StreamService,
        audio_service: AudioService,
        talkback_service: TalkbackService,
    ) -> None:
        """Initialize main window.

        Args:
            camera_service: Camera service
            discovery_service: Discovery service
            stream_service: Stream service
            audio_service: Audio service for playback/capture
            talkback_service: Service for sending audio to cameras
        """
        super().__init__()

        self.camera_service = camera_service
        self.discovery_service = discovery_service
        self.stream_service = stream_service
        self.audio_service = audio_service
        self.talkback_service = talkback_service

        # Update service
        self.update_service = UpdateService(__version__)
        self.update_service.update_available.connect(self._on_update_available)
        self.update_service.no_update.connect(self._on_no_update)
        self.update_service.check_failed.connect(self._on_update_check_failed)

        self._setup_ui()
        self._connect_signals()
        self._load_cameras()

        # Check for updates on startup (silent)
        self.update_service.check_for_updates()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.setWindowTitle("D-IPCam - Camera Viewer")
        self.setMinimumSize(1024, 768)
        self.resize(1280, 720)

        # Dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                padding: 4px;
                spacing: 8px;
            }
            QToolBar QLabel {
                color: #fff;
                padding: 0 8px;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #fff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #fff;
                selection-background-color: #0078d4;
            }
        """)

        # Toolbar
        self._create_toolbar()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar (camera list)
        self.camera_list = CameraListWidget(self.camera_service)
        layout.addWidget(self.camera_list)

        # Main area (camera grid)
        self.camera_grid = CameraGrid(
            self.stream_service,
            self.audio_service,
            self.talkback_service,
            columns=2
        )
        layout.addWidget(self.camera_grid, stretch=1)

    def _create_toolbar(self) -> None:
        """Create the toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Grid layout selector
        toolbar.addWidget(QLabel("Grid:"))

        self.grid_combo = QComboBox()
        self.grid_combo.addItems(["1x1", "2x2", "3x3", "4x4"])
        self.grid_combo.setCurrentIndex(1)  # Default 2x2
        self.grid_combo.currentIndexChanged.connect(self._on_grid_changed)
        toolbar.addWidget(self.grid_combo)

        toolbar.addSeparator()

        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._refresh_streams)
        toolbar.addAction(refresh_action)

        # Stop all action
        stop_action = QAction("Stop All", self)
        stop_action.triggered.connect(self._stop_all_streams)
        toolbar.addAction(stop_action)

        toolbar.addSeparator()

        # Check for updates action
        self.update_action = QAction("Check for Updates", self)
        self.update_action.triggered.connect(self._check_for_updates)
        toolbar.addAction(self.update_action)

        # Spacer
        spacer = QWidget()
        spacer.setFixedWidth(20)
        toolbar.addWidget(spacer)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.camera_list.add_camera_clicked.connect(self._show_add_camera_dialog)
        self.camera_list.scan_clicked.connect(self._show_discovery_dialog)
        self.camera_list.camera_selected.connect(self._on_camera_selected)
        self.camera_list.camera_edit_requested.connect(self._show_edit_camera_dialog)
        self.camera_list.camera_delete_requested.connect(self._delete_camera)

    def _load_cameras(self) -> None:
        """Load cameras from database."""
        self.camera_list.refresh()

        cameras = self.camera_service.get_enabled_cameras()
        self.camera_grid.set_cameras(cameras)

    def _on_grid_changed(self, index: int) -> None:
        """Handle grid layout change.

        Args:
            index: Combo box index
        """
        columns = index + 1  # 1x1, 2x2, 3x3, 4x4
        self.camera_grid.set_columns(columns)

    def _show_add_camera_dialog(self) -> None:
        """Show dialog to add a new camera."""
        dialog = AddCameraDialog(parent=self)

        if dialog.exec() == AddCameraDialog.DialogCode.Accepted:
            camera = dialog.get_camera()
            if camera:
                saved = self.camera_service.add_camera(
                    name=camera.name,
                    ip=camera.ip,
                    username=camera.username,
                    password=camera.password,
                    port=camera.port,
                    channel=camera.channel,
                )
                self.camera_grid.add_camera(saved)

    def _show_discovery_dialog(self) -> None:
        """Show camera discovery dialog."""
        dialog = DiscoveryDialog(self.discovery_service, parent=self)
        dialog.camera_selected.connect(self._on_discovered_camera_selected)
        dialog.exec()

    def _on_discovered_camera_selected(self, discovered: DiscoveredCamera) -> None:
        """Handle discovered camera selection.

        Args:
            discovered: Discovered camera info
        """
        # Check if already exists
        if self.camera_service.camera_exists(discovered.ip):
            QMessageBox.information(
                self,
                "Camera Exists",
                f"A camera with IP {discovered.ip} already exists."
            )
            return

        # Show add dialog pre-populated with IP
        camera = Camera(
            name=f"Camera {discovered.ip.split('.')[-1]}",
            ip=discovered.ip,
        )

        dialog = AddCameraDialog(camera, parent=self)

        if dialog.exec() == AddCameraDialog.DialogCode.Accepted:
            camera = dialog.get_camera()
            if camera:
                saved = self.camera_service.add_camera(
                    name=camera.name,
                    ip=camera.ip,
                    username=camera.username,
                    password=camera.password,
                    port=camera.port,
                    channel=camera.channel,
                )
                self.camera_grid.add_camera(saved)

    def _on_camera_selected(self, camera: Camera) -> None:
        """Handle camera selection from list.

        Args:
            camera: Selected camera
        """
        # For now, just ensure it's in the grid
        if camera.id and not self.stream_service.is_streaming(camera.id):
            self.camera_grid.add_camera(camera)

    def _refresh_streams(self) -> None:
        """Refresh all camera streams."""
        cameras = self.camera_service.get_enabled_cameras()
        self.camera_grid.set_cameras(cameras)

    def _stop_all_streams(self) -> None:
        """Stop all camera streams."""
        self.camera_grid.clear()

    def _show_edit_camera_dialog(self, camera: Camera) -> None:
        """Show dialog to edit an existing camera.

        Args:
            camera: Camera to edit
        """
        dialog = AddCameraDialog(camera, parent=self)

        if dialog.exec() == AddCameraDialog.DialogCode.Accepted:
            updated_camera = dialog.get_camera()
            if updated_camera:
                # Stop stream if running
                if camera.id:
                    self.camera_grid.remove_camera(camera.id)

                # Update camera
                self.camera_service.update_camera(updated_camera)

                # Restart stream with new settings
                if updated_camera.enabled:
                    self.camera_grid.add_camera(updated_camera)

    def _delete_camera(self, camera: Camera) -> None:
        """Delete a camera after confirmation.

        Args:
            camera: Camera to delete
        """
        reply = QMessageBox.question(
            self,
            "Delete Camera",
            f"Are you sure you want to delete '{camera.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if camera.id:
                self.camera_grid.remove_camera(camera.id)
                self.camera_service.delete_camera(camera.id)

    def _check_for_updates(self) -> None:
        """Manually check for updates."""
        self.update_action.setEnabled(False)
        self.update_action.setText("Checking...")
        self._manual_update_check = True
        self.update_service.check_for_updates()

    def _on_update_available(self, release: ReleaseInfo) -> None:
        """Handle update available signal.

        Args:
            release: Release info
        """
        self.update_action.setEnabled(True)
        self.update_action.setText("Check for Updates")

        dialog = UpdateDialog(release, __version__, parent=self)
        dialog.exec()

    def _on_no_update(self, current_version: str) -> None:
        """Handle no update signal.

        Args:
            current_version: Current version
        """
        self.update_action.setEnabled(True)
        self.update_action.setText("Check for Updates")

        # Only show message if manually triggered
        if getattr(self, '_manual_update_check', False):
            self._manual_update_check = False
            QMessageBox.information(
                self,
                "No Updates",
                f"You're running the latest version (v{current_version})."
            )

    def _on_update_check_failed(self, error: str) -> None:
        """Handle update check failed signal.

        Args:
            error: Error message
        """
        self.update_action.setEnabled(True)
        self.update_action.setText("Check for Updates")

        # Only show message if manually triggered
        if getattr(self, '_manual_update_check', False):
            self._manual_update_check = False
            QMessageBox.warning(
                self,
                "Update Check Failed",
                f"Could not check for updates: {error}"
            )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.stream_service.stop_all_streams()
        self.audio_service.stop_all()
        self.talkback_service.stop_all()
        super().closeEvent(event)
