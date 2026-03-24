"""Stream service for RTSP video and audio capture using PyAV."""

import av
import numpy as np
from typing import Dict

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex, QMutexLocker

from d_ipcam.data.models import Camera
from d_ipcam.core.constants import CameraStatus


class StreamWorker(QThread):
    """Worker thread for capturing RTSP stream with audio."""

    frame_ready = pyqtSignal(int, np.ndarray)  # camera_id, frame
    audio_ready = pyqtSignal(int, bytes, int, int)  # camera_id, audio_data, sample_rate, channels
    status_changed = pyqtSignal(int, CameraStatus)  # camera_id, status
    error_occurred = pyqtSignal(int, str)  # camera_id, error message

    def __init__(self, camera: Camera) -> None:
        """Initialize stream worker.

        Args:
            camera: Camera to stream from
        """
        super().__init__()
        self.camera = camera
        self._stop_requested = False
        self._mutex = QMutex()

    def run(self) -> None:
        """Capture frames and audio from RTSP stream."""
        camera_id = self.camera.id

        self.status_changed.emit(camera_id, CameraStatus.CONNECTING)

        rtsp_url = self.camera.get_rtsp_url()

        try:
            # Open RTSP stream with PyAV
            container = av.open(
                rtsp_url,
                options={
                    'rtsp_transport': 'tcp',
                    'stimeout': '5000000',  # 5 second timeout
                    'buffer_size': '1024000',
                }
            )

            # Find video and audio streams
            video_stream = None
            audio_stream = None

            for stream in container.streams:
                if stream.type == 'video' and video_stream is None:
                    video_stream = stream
                elif stream.type == 'audio' and audio_stream is None:
                    audio_stream = stream

            if video_stream is None:
                self.status_changed.emit(camera_id, CameraStatus.ERROR)
                self.error_occurred.emit(camera_id, "No video stream found")
                return

            self.status_changed.emit(camera_id, CameraStatus.ONLINE)

            # Get audio info if available
            audio_sample_rate = 8000
            audio_channels = 1
            if audio_stream:
                audio_sample_rate = audio_stream.codec_context.sample_rate or 8000
                audio_channels = audio_stream.codec_context.channels or 1

            # Create resampler for audio (convert to s16 PCM)
            audio_resampler = None
            if audio_stream:
                audio_resampler = av.AudioResampler(
                    format='s16',
                    layout='mono' if audio_channels == 1 else 'stereo',
                    rate=audio_sample_rate,
                )

            consecutive_failures = 0
            max_failures = 30

            # Demux and decode
            for packet in container.demux(video_stream, audio_stream) if audio_stream else container.demux(video_stream):
                if self._stop_requested:
                    break

                try:
                    if packet.stream == video_stream:
                        for frame in packet.decode():
                            # Convert to numpy array (BGR for OpenCV compatibility)
                            img = frame.to_ndarray(format='bgr24')
                            self.frame_ready.emit(camera_id, img)
                            consecutive_failures = 0

                    elif packet.stream == audio_stream and audio_resampler:
                        for frame in packet.decode():
                            # Resample to consistent format
                            resampled = audio_resampler.resample(frame)
                            for resampled_frame in resampled:
                                # Convert to bytes
                                audio_bytes = bytes(resampled_frame.planes[0])
                                self.audio_ready.emit(
                                    camera_id,
                                    audio_bytes,
                                    audio_sample_rate,
                                    audio_channels
                                )

                except av.error.EOFError:
                    break
                except Exception as e:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        self.status_changed.emit(camera_id, CameraStatus.ERROR)
                        self.error_occurred.emit(camera_id, f"Stream error: {e}")
                        break

            container.close()

        except av.error.HTTPError as e:
            self.status_changed.emit(camera_id, CameraStatus.ERROR)
            self.error_occurred.emit(camera_id, f"Connection failed: {e}")
        except av.error.InvalidDataError as e:
            self.status_changed.emit(camera_id, CameraStatus.ERROR)
            self.error_occurred.emit(camera_id, f"Invalid stream: {e}")
        except Exception as e:
            self.status_changed.emit(camera_id, CameraStatus.ERROR)
            self.error_occurred.emit(camera_id, f"Error: {e}")

        self.status_changed.emit(camera_id, CameraStatus.OFFLINE)

    def stop(self) -> None:
        """Request the worker to stop."""
        with QMutexLocker(self._mutex):
            self._stop_requested = True


class StreamService(QObject):
    """Service for managing camera streams."""

    # Signals
    frame_ready = pyqtSignal(int, np.ndarray)  # camera_id, frame
    audio_ready = pyqtSignal(int, bytes, int, int)  # camera_id, audio_data, sample_rate, channels
    status_changed = pyqtSignal(int, CameraStatus)  # camera_id, status
    error_occurred = pyqtSignal(int, str)  # camera_id, error message

    def __init__(self) -> None:
        """Initialize stream service."""
        super().__init__()
        self._workers: Dict[int, StreamWorker] = {}

    def start_stream(self, camera: Camera) -> None:
        """Start streaming from a camera.

        Args:
            camera: Camera to stream from
        """
        if camera.id is None:
            return

        # Stop existing stream if any
        if camera.id in self._workers:
            self.stop_stream(camera.id)

        worker = StreamWorker(camera)
        worker.frame_ready.connect(self.frame_ready.emit)
        worker.audio_ready.connect(self.audio_ready.emit)
        worker.status_changed.connect(self.status_changed.emit)
        worker.error_occurred.connect(self.error_occurred.emit)

        self._workers[camera.id] = worker
        worker.start()

    def stop_stream(self, camera_id: int) -> None:
        """Stop streaming from a camera.

        Args:
            camera_id: Camera ID to stop
        """
        if camera_id in self._workers:
            worker = self._workers[camera_id]
            worker.stop()
            worker.wait(5000)  # Wait up to 5 seconds
            del self._workers[camera_id]

    def stop_all_streams(self) -> None:
        """Stop all active streams."""
        for camera_id in list(self._workers.keys()):
            self.stop_stream(camera_id)

    def is_streaming(self, camera_id: int) -> bool:
        """Check if a camera is currently streaming.

        Args:
            camera_id: Camera ID to check

        Returns:
            True if streaming
        """
        return camera_id in self._workers and self._workers[camera_id].isRunning()

    def get_active_streams(self) -> list[int]:
        """Get list of active stream camera IDs.

        Returns:
            List of camera IDs with active streams
        """
        return [
            cid for cid, worker in self._workers.items()
            if worker.isRunning()
        ]
