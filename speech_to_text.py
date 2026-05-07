from __future__ import annotations

from pathlib import Path
import time
import wave

from config import Settings, SETTINGS
from logging_config import get_logger


logger = get_logger("speech_to_text")
_MODEL_CACHE: dict[tuple[str, str, str, str], object] = {}


class SpeechToText:
    def __init__(
        self,
        settings: Settings = SETTINGS,
        mock_command: str | None = None,
    ) -> None:
        self.settings = settings
        self.mock_command = mock_command

    def listen(self) -> str | None:
        if self.settings.test_mode or not self.settings.voice_enabled:
            return self._mock_listen()

        audio_path = self.record_microphone()
        if audio_path is None:
            return None
        return self.transcribe_audio_file(audio_path)

    def record_microphone(self) -> Path | None:
        try:
            import numpy as np
            import sounddevice as sd
        except Exception as exc:
            logger.error("Microphone dependencies unavailable: %s", exc)
            return None

        duration = max(0.5, float(self.settings.phrase_time_limit))
        sample_rate = self.settings.microphone_sample_rate
        channels = self.settings.microphone_channels
        logger.info("Listening for %.1f seconds", duration)

        try:
            audio = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                dtype="float32",
            )
            sd.wait()
        except Exception as exc:
            logger.error("Microphone recording failed: %s", exc)
            return None

        audio = np.squeeze(audio)
        audio_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)
        self.settings.recordings_dir.mkdir(parents=True, exist_ok=True)
        path = self.settings.recordings_dir / f"command_{int(time.time())}.wav"
        self._write_wav(path, audio_int16, sample_rate)
        return path

    def transcribe_audio_file(self, audio_path: str | Path) -> str | None:
        model = self._get_model()
        started = time.perf_counter()
        segments, _info = model.transcribe(
            str(audio_path),
            language=self.settings.voice_language or None,
            beam_size=1,
            vad_filter=True,
            without_timestamps=True,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info("Whisper transcription finished in %.0f ms: %s", elapsed_ms, text)
        return text.lower() if text else None

    def _get_model(self) -> object:
        cache_key = (
            self.settings.whisper_model_size,
            self.settings.whisper_device,
            self.settings.whisper_compute_type,
            str(self.settings.models_dir),
        )
        if cache_key in _MODEL_CACHE:
            return _MODEL_CACHE[cache_key]

        from faster_whisper import WhisperModel

        download_root = self.settings.models_dir / "faster-whisper"
        download_root.mkdir(parents=True, exist_ok=True)
        logger.info("Loading faster-whisper model '%s'", self.settings.whisper_model_size)
        model = WhisperModel(
            self.settings.whisper_model_size,
            device=self.settings.whisper_device,
            compute_type=self.settings.whisper_compute_type,
            cpu_threads=self.settings.whisper_cpu_threads,
            download_root=str(download_root),
        )
        _MODEL_CACHE[cache_key] = model
        return model

    def _mock_listen(self) -> str | None:
        if self.mock_command is not None:
            logger.info("Mock command provided: %s", self.mock_command)
            return self.mock_command.strip().lower() or None

        if self.settings.mock_command:
            logger.info("Mock command from settings: %s", self.settings.mock_command)
            return self.settings.mock_command.strip().lower() or None

        if self.settings.non_interactive:
            logger.info("Non-interactive mock listen returned no command")
            return None

        try:
            command = input("Type command: ").strip()
        except EOFError:
            return None
        return command.lower() if command else None

    @staticmethod
    def _write_wav(path: Path, samples: object, sample_rate: int) -> None:
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())


def listen(mock_command: str | None = None) -> str | None:
    return SpeechToText(mock_command=mock_command).listen()
