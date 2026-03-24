"""Audio service for playback and microphone capture using Qt Multimedia."""

from enum import Enum, auto
from typing import Dict

from PyQt6.QtCore import QObject, QByteArray, QIODevice, pyqtSignal
from PyQt6.QtMultimedia import (
    QAudioFormat,
    QAudioSink,
    QAudioSource,
    QMediaDevices,
)


class TalkMode(Enum):
    """Talk mode options."""
    PUSH_TO_TALK = auto()  # Hold to talk
    TOGGLE = auto()        # Click to toggle on/off


class AudioPlayer(QObject):
    """Audio player for a single camera stream."""

    def __init__(self, camera_id: int, parent: QObject | None = None) -> None:
        """Initialize audio player.

        Args:
            camera_id: Camera ID this player is for
            parent: Parent QObject
        """
        super().__init__(parent)
        self.camera_id = camera_id
        self._sink: QAudioSink | None = None
        self._device: QIODevice | None = None
        self._muted = True
        self._format: QAudioFormat | None = None

    def setup(self, sample_rate: int = 8000, channels: int = 1) -> bool:
        """Set up audio output.

        Args:
            sample_rate: Audio sample rate (typically 8000 for cameras)
            channels: Number of audio channels

        Returns:
            True if setup successful
        """
        # Create audio format
        self._format = QAudioFormat()
        self._format.setSampleRate(sample_rate)
        self._format.setChannelCount(channels)
        self._format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        # Get default output device
        device = QMediaDevices.defaultAudioOutput()
        if device.isNull():
            return False

        # Create audio sink
        self._sink = QAudioSink(device, self._format)
        self._device = self._sink.start()

        return self._device is not None

    def write(self, audio_data: bytes) -> None:
        """Write audio data to output.

        Args:
            audio_data: Raw PCM audio bytes
        """
        if self._device and not self._muted:
            self._device.write(audio_data)

    def set_muted(self, muted: bool) -> None:
        """Set mute state.

        Args:
            muted: True to mute
        """
        self._muted = muted

    def is_muted(self) -> bool:
        """Check if muted.

        Returns:
            True if muted
        """
        return self._muted

    def stop(self) -> None:
        """Stop audio playback."""
        if self._sink:
            self._sink.stop()
            self._sink = None
            self._device = None


class MicrophoneCapture(QObject):
    """Microphone capture for two-way audio."""

    # Signal emitted with captured audio data
    audio_captured = pyqtSignal(bytes)

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize microphone capture.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._source: QAudioSource | None = None
        self._device: QIODevice | None = None
        self._active = False
        self._talk_mode = TalkMode.PUSH_TO_TALK

    def setup(self, sample_rate: int = 8000, channels: int = 1) -> bool:
        """Set up microphone input.

        Args:
            sample_rate: Audio sample rate
            channels: Number of channels

        Returns:
            True if setup successful
        """
        # Create audio format matching camera requirements
        audio_format = QAudioFormat()
        audio_format.setSampleRate(sample_rate)
        audio_format.setChannelCount(channels)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        # Get default input device
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            return False

        # Create audio source
        self._source = QAudioSource(device, audio_format)
        return True

    def start(self) -> None:
        """Start capturing audio."""
        if self._source and not self._active:
            self._device = self._source.start()
            if self._device:
                self._device.readyRead.connect(self._on_data_ready)
                self._active = True

    def stop(self) -> None:
        """Stop capturing audio."""
        if self._source and self._active:
            self._source.stop()
            self._active = False
            if self._device:
                self._device.readyRead.disconnect(self._on_data_ready)
            self._device = None

    def _on_data_ready(self) -> None:
        """Handle incoming audio data."""
        if self._device:
            data = self._device.readAll()
            if data:
                self.audio_captured.emit(bytes(data.data()))

    def is_active(self) -> bool:
        """Check if capture is active.

        Returns:
            True if capturing
        """
        return self._active

    def set_talk_mode(self, mode: TalkMode) -> None:
        """Set talk mode.

        Args:
            mode: Talk mode
        """
        self._talk_mode = mode

    def get_talk_mode(self) -> TalkMode:
        """Get current talk mode.

        Returns:
            Current talk mode
        """
        return self._talk_mode


class AudioService(QObject):
    """Service for managing audio playback and capture."""

    # Signals
    mic_data_ready = pyqtSignal(int, bytes)  # camera_id, audio_data

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize audio service.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._players: Dict[int, AudioPlayer] = {}
        self._mic = MicrophoneCapture(self)
        self._active_talk_camera: int | None = None
        self._mute_on_talk = False

    def setup_player(
        self,
        camera_id: int,
        sample_rate: int = 8000,
        channels: int = 1
    ) -> bool:
        """Set up audio player for a camera.

        Args:
            camera_id: Camera ID
            sample_rate: Audio sample rate
            channels: Number of channels

        Returns:
            True if setup successful
        """
        if camera_id in self._players:
            return True

        player = AudioPlayer(camera_id, self)
        if player.setup(sample_rate, channels):
            self._players[camera_id] = player
            return True
        return False

    def play_audio(self, camera_id: int, audio_data: bytes) -> None:
        """Play audio data for a camera.

        Args:
            camera_id: Camera ID
            audio_data: Raw PCM audio bytes
        """
        if camera_id in self._players:
            # Mute if talking to this camera and mute_on_talk is enabled
            if self._mute_on_talk and self._active_talk_camera == camera_id:
                return
            self._players[camera_id].write(audio_data)

    def set_listen_enabled(self, camera_id: int, enabled: bool) -> None:
        """Enable/disable listening to camera audio.

        Args:
            camera_id: Camera ID
            enabled: True to enable listening
        """
        if camera_id in self._players:
            self._players[camera_id].set_muted(not enabled)

    def is_listening(self, camera_id: int) -> bool:
        """Check if listening to camera audio.

        Args:
            camera_id: Camera ID

        Returns:
            True if listening (not muted)
        """
        if camera_id in self._players:
            return not self._players[camera_id].is_muted()
        return False

    def start_talk(self, camera_id: int) -> None:
        """Start talking to a camera.

        Args:
            camera_id: Camera ID to talk to
        """
        if not self._mic.is_active():
            self._mic.setup()
            self._mic.audio_captured.connect(self._on_mic_data)
            self._mic.start()

        self._active_talk_camera = camera_id

    def stop_talk(self) -> None:
        """Stop talking."""
        if self._mic.is_active():
            self._mic.stop()
        self._active_talk_camera = None

    def is_talking(self, camera_id: int | None = None) -> bool:
        """Check if talking.

        Args:
            camera_id: Optional camera ID to check specific camera

        Returns:
            True if talking (to specified camera or any)
        """
        if camera_id is not None:
            return self._active_talk_camera == camera_id
        return self._active_talk_camera is not None

    def set_talk_mode(self, mode: TalkMode) -> None:
        """Set talk mode.

        Args:
            mode: Talk mode
        """
        self._mic.set_talk_mode(mode)

    def get_talk_mode(self) -> TalkMode:
        """Get current talk mode.

        Returns:
            Current talk mode
        """
        return self._mic.get_talk_mode()

    def set_mute_on_talk(self, enabled: bool) -> None:
        """Set whether to mute camera audio when talking.

        Args:
            enabled: True to mute camera when talking
        """
        self._mute_on_talk = enabled

    def _on_mic_data(self, data: bytes) -> None:
        """Handle captured microphone data.

        Args:
            data: Audio data bytes
        """
        if self._active_talk_camera is not None:
            self.mic_data_ready.emit(self._active_talk_camera, data)

    def stop_player(self, camera_id: int) -> None:
        """Stop and remove audio player for a camera.

        Args:
            camera_id: Camera ID
        """
        if camera_id in self._players:
            self._players[camera_id].stop()
            del self._players[camera_id]

    def stop_all(self) -> None:
        """Stop all audio playback and capture."""
        self.stop_talk()
        for player in self._players.values():
            player.stop()
        self._players.clear()
