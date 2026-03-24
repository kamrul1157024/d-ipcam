"""Dialog widgets for camera management."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QCheckBox,
    QComboBox,
    QGroupBox,
)

from d_ipcam.data.models import Camera
from d_ipcam.core.constants import StreamQuality
from d_ipcam.services import DiscoveryService
from d_ipcam.services.discovery_service import DiscoveredCamera


class AddCameraDialog(QDialog):
    """Dialog for adding or editing a camera."""

    def __init__(
        self,
        camera: Camera | None = None,
        parent=None,
    ) -> None:
        """Initialize add camera dialog.

        Args:
            camera: Camera to edit, or None for new camera
            parent: Parent widget
        """
        super().__init__(parent)
        self.camera = camera
        self._is_edit = camera is not None

        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.setWindowTitle("Edit Camera" if self._is_edit else "Add Camera")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #fff;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #3d3d3d;
                color: #fff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #fff;
                selection-background-color: #0078d4;
            }
            QGroupBox {
                color: #aaa;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Form - Basic settings
        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Living Room Camera")
        form.addRow("Name:", self.name_input)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        form.addRow("IP Address:", self.ip_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("admin")
        form.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("••••••••")
        form.addRow("Password:", self.password_input)

        # Quality dropdown
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Sub Stream (Recommended)", StreamQuality.SUB.value)
        self.quality_combo.addItem("Main Stream (High Quality)", StreamQuality.MAIN.value)
        form.addRow("Quality:", self.quality_combo)

        layout.addLayout(form)

        # Advanced Settings (collapsible)
        self.advanced_group = QGroupBox("Advanced Settings")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)
        advanced_layout = QFormLayout(self.advanced_group)
        advanced_layout.setSpacing(8)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(554)
        advanced_layout.addRow("RTSP Port:", self.port_input)

        self.channel_input = QSpinBox()
        self.channel_input.setRange(1, 16)
        self.channel_input.setValue(1)
        self.channel_input.setToolTip("Channel 1 for standalone cameras, 1-16 for NVR")
        advanced_layout.addRow("Channel:", self.channel_input)

        self.subtype_input = QSpinBox()
        self.subtype_input.setRange(0, 3)
        self.subtype_input.setValue(1)
        self.subtype_input.setToolTip("0=Main, 1=Sub, 2=Stream3, 3=Stream4")
        advanced_layout.addRow("Subtype:", self.subtype_input)

        # Connect quality combo to subtype
        self.quality_combo.currentIndexChanged.connect(self._on_quality_changed)

        layout.addWidget(self.advanced_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._button_style("#666666"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if self._is_edit else "Add")
        save_btn.setStyleSheet(self._button_style("#0078d4"))
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _on_quality_changed(self, index: int) -> None:
        """Sync quality dropdown with subtype spinbox."""
        subtype = self.quality_combo.currentData()
        self.subtype_input.setValue(subtype)

    def _button_style(self, color: str) -> str:
        """Get button stylesheet."""
        # Ensure 6-digit hex for alpha suffix to work
        if len(color) == 4:  # #RGB -> #RRGGBB
            color = f"#{color[1]*2}{color[2]*2}{color[3]*2}"
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {color}cc;
            }}
        """

    def _populate_fields(self) -> None:
        """Populate form fields from camera."""
        if self.camera:
            self.name_input.setText(self.camera.name)
            self.ip_input.setText(self.camera.ip)
            self.username_input.setText(self.camera.username)
            self.password_input.setText(self.camera.password)

            # Set quality dropdown based on subtype
            if self.camera.subtype == 0:
                self.quality_combo.setCurrentIndex(1)  # Main stream
            else:
                self.quality_combo.setCurrentIndex(0)  # Sub stream

            # Advanced settings
            self.port_input.setValue(self.camera.port)
            self.channel_input.setValue(self.camera.channel)
            self.subtype_input.setValue(self.camera.subtype)

    def _on_save(self) -> None:
        """Handle save button click."""
        name = self.name_input.text().strip()
        ip = self.ip_input.text().strip()

        if not name or not ip:
            return

        # Get subtype from advanced settings if expanded, otherwise from quality dropdown
        if self.advanced_group.isChecked():
            subtype = self.subtype_input.value()
        else:
            subtype = self.quality_combo.currentData()

        if self.camera:
            self.camera.name = name
            self.camera.ip = ip
            self.camera.username = self.username_input.text()
            self.camera.password = self.password_input.text()
            self.camera.port = self.port_input.value()
            self.camera.channel = self.channel_input.value()
            self.camera.subtype = subtype
        else:
            self.camera = Camera(
                name=name,
                ip=ip,
                username=self.username_input.text(),
                password=self.password_input.text(),
                port=self.port_input.value(),
                channel=self.channel_input.value(),
                subtype=subtype,
            )

        self.accept()

    def get_camera(self) -> Camera | None:
        """Get the camera from the dialog.

        Returns:
            Camera instance or None if cancelled
        """
        return self.camera


class DiscoveryDialog(QDialog):
    """Dialog for discovering cameras on the network."""

    camera_selected = pyqtSignal(DiscoveredCamera)

    def __init__(
        self,
        discovery_service: DiscoveryService,
        parent=None,
    ) -> None:
        """Initialize discovery dialog.

        Args:
            discovery_service: Discovery service
            parent: Parent widget
        """
        super().__init__(parent)
        self.discovery_service = discovery_service
        self._discovered: list[DiscoveredCamera] = []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.setWindowTitle("Discover Cameras")
        self.setMinimumSize(450, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #fff;
            }
            QListWidget {
                background-color: #3d3d3d;
                color: #fff;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header
        header = QLabel("Scanning network for Dahua cameras...")
        header.setStyleSheet("font-size: 14px;")
        layout.addWidget(header)
        self.header_label = header

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 254)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Results list
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Buttons
        button_layout = QHBoxLayout()

        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.setStyleSheet(self._button_style("#0078d4"))
        self.scan_btn.clicked.connect(self._toggle_scan)
        button_layout.addWidget(self.scan_btn)

        button_layout.addStretch()

        self.add_btn = QPushButton("Add Selected")
        self.add_btn.setStyleSheet(self._button_style("#28a745"))
        self.add_btn.clicked.connect(self._add_selected)
        self.add_btn.setEnabled(False)
        button_layout.addWidget(self.add_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(self._button_style("#666666"))
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _button_style(self, color: str) -> str:
        """Get button stylesheet."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}cc;
            }}
            QPushButton:disabled {{
                background-color: #555;
            }}
        """

    def _connect_signals(self) -> None:
        """Connect service signals."""
        self.discovery_service.camera_found.connect(self._on_camera_found)
        self.discovery_service.scan_progress.connect(self._on_progress)
        self.discovery_service.scan_complete.connect(self._on_complete)
        self.discovery_service.scan_error.connect(self._on_error)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _toggle_scan(self) -> None:
        """Toggle scanning on/off."""
        if self.discovery_service.is_scanning():
            self.discovery_service.stop_scan()
            self.scan_btn.setText("Start Scan")
        else:
            self.list_widget.clear()
            self._discovered.clear()
            self.discovery_service.start_scan()
            self.scan_btn.setText("Stop Scan")
            self.header_label.setText("Scanning network for Dahua cameras...")

    def _on_camera_found(self, camera: DiscoveredCamera) -> None:
        """Handle camera found signal.

        Args:
            camera: Discovered camera
        """
        self._discovered.append(camera)

        ports_str = ", ".join(str(p) for p in camera.open_ports)
        label = f"{'[DAHUA] ' if camera.is_dahua else ''}{camera.ip} (ports: {ports_str})"

        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, len(self._discovered) - 1)

        if camera.is_dahua:
            item.setForeground(Qt.GlobalColor.green)

        self.list_widget.addItem(item)

    def _on_progress(self, current: int, total: int) -> None:
        """Handle scan progress.

        Args:
            current: Current progress
            total: Total items
        """
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_complete(self, cameras: list) -> None:
        """Handle scan complete.

        Args:
            cameras: List of discovered cameras
        """
        self.scan_btn.setText("Start Scan")
        dahua_count = sum(1 for c in cameras if c.is_dahua)
        self.header_label.setText(
            f"Found {len(cameras)} devices, {dahua_count} Dahua cameras"
        )

    def _on_error(self, error: str) -> None:
        """Handle scan error.

        Args:
            error: Error message
        """
        self.scan_btn.setText("Start Scan")
        self.header_label.setText(f"Error: {error}")

    def _on_selection_changed(self) -> None:
        """Handle list selection change."""
        self.add_btn.setEnabled(len(self.list_widget.selectedItems()) > 0)

    def _add_selected(self) -> None:
        """Add selected cameras."""
        for item in self.list_widget.selectedItems():
            index = item.data(Qt.ItemDataRole.UserRole)
            if 0 <= index < len(self._discovered):
                self.camera_selected.emit(self._discovered[index])
