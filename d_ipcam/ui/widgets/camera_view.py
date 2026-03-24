"""Single camera view widget with audio controls."""

import cv2
import numpy as np

from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMenu,
    QSizePolicy,
)

from d_ipcam.core.constants import CameraStatus
from d_ipcam.data.models import Camera
from d_ipcam.services.audio_service import TalkMode


class CameraView(QWidget):
    """Widget for displaying a single camera stream with audio controls."""

    # Signals for audio control
    listen_toggled = pyqtSignal(int, bool)  # camera_id, enabled
    talk_started = pyqtSignal(int)  # camera_id
    talk_stopped = pyqtSignal(int)  # camera_id
    talk_mode_changed = pyqtSignal(int, TalkMode)  # camera_id, mode

    def __init__(
        self,
        camera: Camera | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize camera view.

        Args:
            camera: Camera to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.camera = camera
        self._status = CameraStatus.OFFLINE
        self._listening = False
        self._talking = False
        self._talk_mode = TalkMode.PUSH_TO_TALK

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.video_label)

        # Control bar
        control_bar = QWidget()
        control_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }
        """)
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(8, 4, 8, 4)
        control_layout.setSpacing(8)

        # Audio listen button
        self.listen_btn = QPushButton("🔇")
        self.listen_btn.setToolTip("Listen to camera audio")
        self.listen_btn.setFixedSize(32, 32)
        self.listen_btn.setStyleSheet(self._audio_button_style(False))
        self.listen_btn.clicked.connect(self._toggle_listen)
        control_layout.addWidget(self.listen_btn)

        # Talk button with dropdown
        self.talk_btn = QPushButton("🎤")
        self.talk_btn.setToolTip("Talk to camera")
        self.talk_btn.setFixedSize(32, 32)
        self.talk_btn.setStyleSheet(self._audio_button_style(False))
        self.talk_btn.pressed.connect(self._on_talk_pressed)
        self.talk_btn.released.connect(self._on_talk_released)
        self.talk_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.talk_btn.customContextMenuRequested.connect(self._show_talk_menu)
        control_layout.addWidget(self.talk_btn)

        control_layout.addStretch()

        # Camera name label
        self.name_label = QLabel()
        self.name_label.setStyleSheet("""
            QLabel {
                color: #fff;
                font-size: 12px;
            }
        """)
        control_layout.addWidget(self.name_label)

        layout.addWidget(control_bar)

        self._update_name_label()
        self._show_status_message()

    def _audio_button_style(self, active: bool) -> str:
        """Get button style for audio controls.

        Args:
            active: Whether the button is in active state

        Returns:
            CSS stylesheet
        """
        bg_color = "#0078d4" if active else "#444444"
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {bg_color}cc;
            }}
            QPushButton:pressed {{
                background-color: {bg_color}99;
            }}
        """

    def set_camera(self, camera: Camera) -> None:
        """Set the camera for this view.

        Args:
            camera: Camera to display
        """
        self.camera = camera
        self._update_name_label()

    def _update_name_label(self) -> None:
        """Update the camera name label."""
        if self.camera:
            self.name_label.setText(f"{self.camera.name}")
        else:
            self.name_label.setText("")

    def _show_status_message(self) -> None:
        """Show status message on the video label."""
        messages = {
            CameraStatus.OFFLINE: "Offline",
            CameraStatus.CONNECTING: "Connecting...",
            CameraStatus.ERROR: "Connection Error",
            CameraStatus.ONLINE: "",
        }

        message = messages.get(self._status, "")
        if message:
            self.video_label.setText(message)
            self.video_label.setStyleSheet("""
                QLabel {
                    background-color: #1a1a1a;
                    border: 1px solid #333;
                    border-radius: 4px;
                    color: #888;
                    font-size: 14px;
                }
            """)

    def _toggle_listen(self) -> None:
        """Toggle listening to camera audio."""
        if self.camera and self.camera.id:
            self._listening = not self._listening
            self._update_listen_button()
            self.listen_toggled.emit(self.camera.id, self._listening)

    def _update_listen_button(self) -> None:
        """Update listen button appearance."""
        self.listen_btn.setText("🔊" if self._listening else "🔇")
        self.listen_btn.setStyleSheet(self._audio_button_style(self._listening))

    def _on_talk_pressed(self) -> None:
        """Handle talk button press."""
        if self.camera and self.camera.id:
            if self._talk_mode == TalkMode.PUSH_TO_TALK:
                self._start_talking()
            else:  # Toggle mode
                if self._talking:
                    self._stop_talking()
                else:
                    self._start_talking()

    def _on_talk_released(self) -> None:
        """Handle talk button release."""
        if self._talk_mode == TalkMode.PUSH_TO_TALK and self._talking:
            self._stop_talking()

    def _start_talking(self) -> None:
        """Start talking to camera."""
        if self.camera and self.camera.id:
            self._talking = True
            self._update_talk_button()
            self.talk_started.emit(self.camera.id)

    def _stop_talking(self) -> None:
        """Stop talking to camera."""
        if self.camera and self.camera.id:
            self._talking = False
            self._update_talk_button()
            self.talk_stopped.emit(self.camera.id)

    def _update_talk_button(self) -> None:
        """Update talk button appearance."""
        if self._talking:
            self.talk_btn.setText("🎤🔴")
        else:
            self.talk_btn.setText("🎤")
        self.talk_btn.setStyleSheet(self._audio_button_style(self._talking))

    def _show_talk_menu(self, pos) -> None:
        """Show talk mode context menu.

        Args:
            pos: Mouse position
        """
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
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QMenu::item:checked {
                background-color: #444;
            }
        """)

        # Push to talk option
        ptt_action = menu.addAction("Push to Talk")
        ptt_action.setCheckable(True)
        ptt_action.setChecked(self._talk_mode == TalkMode.PUSH_TO_TALK)
        ptt_action.triggered.connect(lambda: self._set_talk_mode(TalkMode.PUSH_TO_TALK))

        # Toggle option
        toggle_action = menu.addAction("Toggle Talk")
        toggle_action.setCheckable(True)
        toggle_action.setChecked(self._talk_mode == TalkMode.TOGGLE)
        toggle_action.triggered.connect(lambda: self._set_talk_mode(TalkMode.TOGGLE))

        menu.exec(self.talk_btn.mapToGlobal(pos))

    def _set_talk_mode(self, mode: TalkMode) -> None:
        """Set talk mode.

        Args:
            mode: Talk mode
        """
        self._talk_mode = mode
        if self.camera and self.camera.id:
            self.talk_mode_changed.emit(self.camera.id, mode)

    @pyqtSlot(CameraStatus)
    def set_status(self, status: CameraStatus) -> None:
        """Update the camera status.

        Args:
            status: New camera status
        """
        self._status = status
        if status != CameraStatus.ONLINE:
            self._show_status_message()

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame: np.ndarray) -> None:
        """Update the displayed frame.

        Args:
            frame: OpenCV frame (BGR format)
        """
        if frame is None:
            return

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get frame dimensions
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        # Create QImage
        qt_image = QImage(
            rgb_frame.data,
            w, h,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        # Scale to fit label while maintaining aspect ratio
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.video_label.setPixmap(scaled_pixmap)

    def set_listening(self, listening: bool) -> None:
        """Set listening state (called from external source).

        Args:
            listening: True if listening
        """
        self._listening = listening
        self._update_listen_button()

    def set_talking(self, talking: bool) -> None:
        """Set talking state (called from external source).

        Args:
            talking: True if talking
        """
        self._talking = talking
        self._update_talk_button()

    def clear(self) -> None:
        """Clear the display."""
        self.video_label.clear()
        self._status = CameraStatus.OFFLINE
        self._listening = False
        self._talking = False
        self._update_listen_button()
        self._update_talk_button()
        self._show_status_message()
