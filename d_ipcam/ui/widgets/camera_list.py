"""Camera list sidebar widget."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QMenu,
)

from d_ipcam.data.models import Camera
from d_ipcam.services import CameraService


class CameraListWidget(QWidget):
    """Sidebar widget for listing and managing cameras."""

    # Signals
    camera_selected = pyqtSignal(Camera)
    camera_edit_requested = pyqtSignal(Camera)
    camera_delete_requested = pyqtSignal(Camera)
    add_camera_clicked = pyqtSignal()
    scan_clicked = pyqtSignal()

    def __init__(
        self,
        camera_service: CameraService,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize camera list widget.

        Args:
            camera_service: Camera service
            parent: Parent widget
        """
        super().__init__(parent)
        self.camera_service = camera_service
        self._cameras: dict[int, Camera] = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QLabel("Cameras")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #fff;
                padding: 4px;
            }
        """)
        layout.addWidget(header)

        # Camera list
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                color: #fff;
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        layout.addWidget(self.list_widget)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.scan_btn = QPushButton("Scan")
        self.scan_btn.setStyleSheet(self._button_style())
        button_layout.addWidget(self.scan_btn)

        self.add_btn = QPushButton("+ Add")
        self.add_btn.setStyleSheet(self._button_style("#28a745"))
        button_layout.addWidget(self.add_btn)

        layout.addLayout(button_layout)

        self.setFixedWidth(200)

    def _button_style(self, color: str = "#0078d4") -> str:
        """Get button stylesheet.

        Args:
            color: Button background color

        Returns:
            CSS stylesheet string
        """
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}cc;
            }}
            QPushButton:pressed {{
                background-color: {color}99;
            }}
        """

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.add_btn.clicked.connect(self.add_camera_clicked.emit)
        self.scan_btn.clicked.connect(self.scan_clicked.emit)

        # Connect to camera service signals
        self.camera_service.camera_added.connect(self._on_camera_added)
        self.camera_service.camera_updated.connect(self._on_camera_updated)
        self.camera_service.camera_deleted.connect(self._on_camera_deleted)

    def refresh(self) -> None:
        """Refresh the camera list from the service."""
        self.list_widget.clear()
        self._cameras.clear()

        cameras = self.camera_service.get_all_cameras()
        for camera in cameras:
            self._add_camera_item(camera)

    def _add_camera_item(self, camera: Camera) -> None:
        """Add a camera to the list.

        Args:
            camera: Camera to add
        """
        if camera.id is None:
            return

        item = QListWidgetItem(f"● {camera.name}")
        item.setData(Qt.ItemDataRole.UserRole, camera.id)

        if not camera.enabled:
            item.setForeground(Qt.GlobalColor.gray)

        self.list_widget.addItem(item)
        self._cameras[camera.id] = camera

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle list item click.

        Args:
            item: Clicked item
        """
        camera_id = item.data(Qt.ItemDataRole.UserRole)
        if camera_id in self._cameras:
            self.camera_selected.emit(self._cameras[camera_id])

    def _on_camera_added(self, camera: Camera) -> None:
        """Handle camera added signal.

        Args:
            camera: Added camera
        """
        self._add_camera_item(camera)

    def _on_camera_updated(self, camera: Camera) -> None:
        """Handle camera updated signal.

        Args:
            camera: Updated camera
        """
        self.refresh()

    def _on_camera_deleted(self, camera_id: int) -> None:
        """Handle camera deleted signal.

        Args:
            camera_id: Deleted camera ID
        """
        self.refresh()

    def get_cameras(self) -> list[Camera]:
        """Get all cameras in the list.

        Returns:
            List of cameras
        """
        return list(self._cameras.values())

    def _show_context_menu(self, position) -> None:
        """Show context menu for camera item.

        Args:
            position: Mouse position
        """
        item = self.list_widget.itemAt(position)
        if item is None:
            return

        camera_id = item.data(Qt.ItemDataRole.UserRole)
        if camera_id not in self._cameras:
            return

        camera = self._cameras[camera_id]

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #fff;
                border: 1px solid #444;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
        """)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.camera_edit_requested.emit(camera))
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.camera_delete_requested.emit(camera))
        menu.addAction(delete_action)

        menu.exec(self.list_widget.mapToGlobal(position))
