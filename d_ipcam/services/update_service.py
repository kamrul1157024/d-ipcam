"""Update service for checking GitHub releases."""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional
from packaging import version

from PyQt6.QtCore import QObject, pyqtSignal, QThread


GITHUB_REPO = "kamrul1157024/d-ipcam"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""
    version: str
    name: str
    body: str  # Release notes
    download_url: str
    html_url: str  # Release page URL
    published_at: str


class UpdateCheckWorker(QThread):
    """Worker thread for checking updates."""

    update_available = pyqtSignal(ReleaseInfo)
    no_update = pyqtSignal(str)  # Current version
    check_failed = pyqtSignal(str)  # Error message

    def __init__(self, current_version: str) -> None:
        super().__init__()
        self._current_version = current_version

    def run(self) -> None:
        """Check for updates in background."""
        try:
            release = self._fetch_latest_release()
            if release is None:
                self.check_failed.emit("No releases found")
                return

            # Compare versions
            current = version.parse(self._current_version.lstrip('v'))
            latest = version.parse(release.version.lstrip('v'))

            if latest > current:
                self.update_available.emit(release)
            else:
                self.no_update.emit(self._current_version)

        except urllib.error.URLError as e:
            self.check_failed.emit(f"Network error: {e.reason}")
        except json.JSONDecodeError:
            self.check_failed.emit("Invalid response from GitHub")
        except Exception as e:
            self.check_failed.emit(str(e))

    def _fetch_latest_release(self) -> Optional[ReleaseInfo]:
        """Fetch latest release info from GitHub API."""
        request = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "D-IPCam-Updater"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())

        # Find macOS DMG asset
        download_url = ""
        for asset in data.get("assets", []):
            if asset["name"].endswith(".dmg"):
                download_url = asset["browser_download_url"]
                break

        return ReleaseInfo(
            version=data["tag_name"],
            name=data["name"],
            body=data.get("body", ""),
            download_url=download_url,
            html_url=data["html_url"],
            published_at=data["published_at"],
        )


class UpdateService(QObject):
    """Service for checking and managing app updates."""

    # Signals
    update_available = pyqtSignal(ReleaseInfo)
    no_update = pyqtSignal(str)  # Current version
    check_failed = pyqtSignal(str)  # Error message
    checking = pyqtSignal()  # Started checking

    def __init__(self, current_version: str) -> None:
        """Initialize update service.

        Args:
            current_version: Current app version (e.g., "0.1.0")
        """
        super().__init__()
        self._current_version = current_version
        self._worker: Optional[UpdateCheckWorker] = None

    @property
    def current_version(self) -> str:
        """Get current app version."""
        return self._current_version

    def check_for_updates(self) -> None:
        """Check for updates asynchronously."""
        if self._worker is not None and self._worker.isRunning():
            return  # Already checking

        self.checking.emit()

        self._worker = UpdateCheckWorker(self._current_version)
        self._worker.update_available.connect(self.update_available.emit)
        self._worker.no_update.connect(self.no_update.emit)
        self._worker.check_failed.connect(self.check_failed.emit)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self) -> None:
        """Clean up worker thread."""
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
