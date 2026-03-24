"""Talkback service for sending audio to cameras via RTSP."""

import av
import numpy as np
from typing import Dict, Optional
from queue import Queue, Empty
from threading import Thread

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex, QMutexLocker

from d_ipcam.data.models import Camera


class TalkbackWorker(QThread):
    """Worker thread for sending audio to camera via RTSP."""

    error_occurred = pyqtSignal(int, str)  # camera_id, error
    connected = pyqtSignal(int)  # camera_id
    disconnected = pyqtSignal(int)  # camera_id

    def __init__(self, camera: Camera) -> None:
        """Initialize talkback worker.

        Args:
            camera: Camera to send audio to
        """
        super().__init__()
        self.camera = camera
        self._stop_requested = False
        self._mutex = QMutex()
        self._audio_queue: Queue = Queue(maxsize=100)
        self._sample_rate = 8000
        self._channels = 1

    def queue_audio(self, audio_data: bytes) -> None:
        """Queue audio data to be sent.

        Args:
            audio_data: PCM s16 audio bytes
        """
        try:
            self._audio_queue.put_nowait(audio_data)
        except:
            pass  # Drop if queue full

    def run(self) -> None:
        """Send audio to camera via RTSP."""
        camera_id = self.camera.id

        try:
            # Dahua cameras support backchannel audio via HTTP CGI
            # Using HTTP API instead of RTSP for talk-back
            import http.client
            import base64

            # Create basic auth header
            auth = base64.b64encode(
                f"{self.camera.username}:{self.camera.password}".encode()
            ).decode()

            self.connected.emit(camera_id)

            while not self._stop_requested:
                try:
                    audio_data = self._audio_queue.get(timeout=0.1)

                    # Convert PCM s16 to G.711 PCMU (mu-law)
                    pcmu_data = self._pcm_to_mulaw(audio_data)

                    # Send via HTTP to Dahua audio endpoint
                    conn = http.client.HTTPConnection(
                        self.camera.ip,
                        80,
                        timeout=5
                    )
                    conn.request(
                        "POST",
                        f"/cgi-bin/audio.cgi?action=postAudio&channel={self.camera.channel}&httptype=singlepart",
                        body=pcmu_data,
                        headers={
                            "Authorization": f"Basic {auth}",
                            "Content-Type": "audio/g711a",
                            "Content-Length": str(len(pcmu_data)),
                        }
                    )
                    response = conn.getresponse()
                    conn.close()

                except Empty:
                    continue
                except Exception as e:
                    # Don't spam errors, just continue
                    pass

        except Exception as e:
            self.error_occurred.emit(camera_id, str(e))

        self.disconnected.emit(camera_id)

    def _pcm_to_mulaw(self, pcm_data: bytes) -> bytes:
        """Convert PCM s16 to G.711 mu-law.

        Args:
            pcm_data: PCM signed 16-bit audio

        Returns:
            G.711 mu-law encoded audio
        """
        # Convert bytes to numpy array
        samples = np.frombuffer(pcm_data, dtype=np.int16)

        # Mu-law compression constants
        MULAW_MAX = 0x1FFF
        MULAW_BIAS = 33

        # Mu-law encoding table
        def encode_mulaw(sample: int) -> int:
            sign = (sample >> 8) & 0x80
            if sign:
                sample = -sample
            sample = min(sample, MULAW_MAX)
            sample += MULAW_BIAS

            exponent = 7
            for i in range(7, 0, -1):
                if sample >= (1 << (i + 3)):
                    exponent = i
                    break
            else:
                exponent = 0

            mantissa = (sample >> (exponent + 3)) & 0x0F
            return ~(sign | (exponent << 4) | mantissa) & 0xFF

        # Encode each sample
        mulaw_bytes = bytes([encode_mulaw(s) for s in samples])
        return mulaw_bytes

    def stop(self) -> None:
        """Request the worker to stop."""
        with QMutexLocker(self._mutex):
            self._stop_requested = True


class TalkbackService(QObject):
    """Service for managing talk-back audio to cameras."""

    # Signals
    error_occurred = pyqtSignal(int, str)  # camera_id, error
    talk_started = pyqtSignal(int)  # camera_id
    talk_stopped = pyqtSignal(int)  # camera_id

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize talkback service.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._workers: Dict[int, TalkbackWorker] = {}
        self._cameras: Dict[int, Camera] = {}

    def start_talkback(self, camera: Camera) -> None:
        """Start talk-back to a camera.

        Args:
            camera: Camera to talk to
        """
        if camera.id is None:
            return

        if camera.id in self._workers:
            return

        worker = TalkbackWorker(camera)
        worker.connected.connect(lambda cid: self.talk_started.emit(cid))
        worker.disconnected.connect(lambda cid: self.talk_stopped.emit(cid))
        worker.error_occurred.connect(self.error_occurred.emit)

        self._workers[camera.id] = worker
        self._cameras[camera.id] = camera
        worker.start()

    def stop_talkback(self, camera_id: int) -> None:
        """Stop talk-back to a camera.

        Args:
            camera_id: Camera ID
        """
        if camera_id in self._workers:
            worker = self._workers.pop(camera_id)
            worker.stop()
            worker.wait(2000)
            self._cameras.pop(camera_id, None)

    def send_audio(self, camera_id: int, audio_data: bytes) -> None:
        """Send audio data to a camera.

        Args:
            camera_id: Camera ID
            audio_data: PCM s16 audio bytes
        """
        if camera_id in self._workers:
            self._workers[camera_id].queue_audio(audio_data)

    def stop_all(self) -> None:
        """Stop all talk-back sessions."""
        for camera_id in list(self._workers.keys()):
            self.stop_talkback(camera_id)
