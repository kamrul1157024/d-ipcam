"""AINanny application entry point."""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from d_ipcam.core.config import get_config
from d_ipcam.data import Database, CameraRepository
from d_ipcam.services import CameraService, DiscoveryService, StreamService, AudioService, TalkbackService
from d_ipcam.ui import MainWindow


def main() -> int:
    """Run the AINanny application.

    Returns:
        Exit code
    """
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AINanny")
    app.setApplicationVersion("0.1.0")

    # Get config
    config = get_config()

    # Initialize data layer
    database = Database(config.db_path)
    camera_repo = CameraRepository(database)

    # Initialize services
    camera_service = CameraService(camera_repo)
    discovery_service = DiscoveryService()
    stream_service = StreamService()
    audio_service = AudioService()
    talkback_service = TalkbackService()

    # Create and show main window
    window = MainWindow(
        camera_service=camera_service,
        discovery_service=discovery_service,
        stream_service=stream_service,
        audio_service=audio_service,
        talkback_service=talkback_service,
    )
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
