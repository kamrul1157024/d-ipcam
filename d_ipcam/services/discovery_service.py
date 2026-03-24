"""Discovery service for finding cameras on the network."""

import socket
import subprocess
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from d_ipcam.core.constants import CAMERA_SCAN_PORTS, DAHUA_PROPRIETARY_PORT


@dataclass
class DiscoveredCamera:
    """A camera discovered on the network."""
    ip: str
    open_ports: list[int]
    is_dahua: bool = False

    def __post_init__(self) -> None:
        """Determine if this is likely a Dahua camera."""
        self.is_dahua = DAHUA_PROPRIETARY_PORT in self.open_ports


class NetworkScanWorker(QThread):
    """Worker thread for network scanning."""

    # Signals
    camera_found = pyqtSignal(DiscoveredCamera)
    scan_progress = pyqtSignal(int, int)  # current, total
    scan_complete = pyqtSignal(list)  # list of DiscoveredCamera
    scan_error = pyqtSignal(str)

    def __init__(
        self,
        subnet: str,
        ports: list[int] | None = None,
        timeout: float = 1.0,
    ) -> None:
        """Initialize scan worker.

        Args:
            subnet: Subnet to scan (e.g., "192.168.68")
            ports: Ports to check for cameras
            timeout: Socket timeout in seconds
        """
        super().__init__()
        self.subnet = subnet
        self.ports = ports or list(CAMERA_SCAN_PORTS)
        self.timeout = timeout
        self._stop_requested = False

    def run(self) -> None:
        """Execute the network scan."""
        discovered = []
        ips_to_scan = [f"{self.subnet}.{i}" for i in range(1, 255)]
        total = len(ips_to_scan)

        try:
            with ThreadPoolExecutor(max_workers=50) as executor:
                future_to_ip = {
                    executor.submit(self._check_host, ip): ip
                    for ip in ips_to_scan
                }

                for i, future in enumerate(as_completed(future_to_ip)):
                    if self._stop_requested:
                        break

                    self.scan_progress.emit(i + 1, total)

                    result = future.result()
                    if result:
                        discovered.append(result)
                        self.camera_found.emit(result)

            self.scan_complete.emit(discovered)

        except Exception as e:
            self.scan_error.emit(str(e))

    def _check_host(self, ip: str) -> DiscoveredCamera | None:
        """Check if a host has camera ports open.

        Args:
            ip: IP address to check

        Returns:
            DiscoveredCamera if camera ports found, None otherwise
        """
        open_ports = []

        for port in self.ports:
            if self._stop_requested:
                return None

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((ip, port))
                sock.close()

                if result == 0:
                    open_ports.append(port)
            except Exception:
                pass

        if open_ports:
            return DiscoveredCamera(ip=ip, open_ports=open_ports)

        return None

    def stop(self) -> None:
        """Request the scan to stop."""
        self._stop_requested = True


class DiscoveryService(QObject):
    """Service for discovering cameras on the network."""

    # Signals (forwarded from worker)
    camera_found = pyqtSignal(DiscoveredCamera)
    scan_progress = pyqtSignal(int, int)
    scan_complete = pyqtSignal(list)
    scan_error = pyqtSignal(str)

    def __init__(self) -> None:
        """Initialize discovery service."""
        super().__init__()
        self._worker: NetworkScanWorker | None = None

    def get_local_subnet(self) -> str | None:
        """Get the local subnet for scanning.

        Returns:
            Subnet string (e.g., "192.168.68") or None
        """
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # Extract subnet (assuming /24)
            parts = local_ip.split(".")
            return ".".join(parts[:3])

        except Exception:
            return None

    def start_scan(self, subnet: str | None = None) -> None:
        """Start scanning for cameras.

        Args:
            subnet: Subnet to scan, or None to auto-detect
        """
        if self._worker and self._worker.isRunning():
            return

        if subnet is None:
            subnet = self.get_local_subnet()

        if subnet is None:
            self.scan_error.emit("Could not determine local subnet")
            return

        self._worker = NetworkScanWorker(subnet)
        self._worker.camera_found.connect(self.camera_found.emit)
        self._worker.scan_progress.connect(self.scan_progress.emit)
        self._worker.scan_complete.connect(self.scan_complete.emit)
        self._worker.scan_error.connect(self.scan_error.emit)
        self._worker.start()

    def stop_scan(self) -> None:
        """Stop the current scan."""
        if self._worker:
            self._worker.stop()
            self._worker.wait()
            self._worker = None

    def is_scanning(self) -> bool:
        """Check if a scan is in progress.

        Returns:
            True if scanning
        """
        return self._worker is not None and self._worker.isRunning()
