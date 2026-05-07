from __future__ import annotations

import atexit
from queue import Queue
from threading import Lock, Thread
from typing import Any

from config import Settings, SETTINGS
from logging_config import get_logger


logger = get_logger("text_to_speech")


class TextToSpeech:
    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings
        self._engine: Any | None = None
        self._queue: Queue[str | None] = Queue()
        self._worker: Thread | None = None
        self._engine_lock = Lock()

    def speak(self, text: str, block: bool | None = None) -> None:
        if not text:
            return

        print(f"[ORB SPEAK] {text}")
        if self.settings.test_mode or not self.settings.tts_enabled:
            return

        should_block = (not self.settings.tts_async) if block is None else block
        if should_block:
            self._speak_blocking(text)
            return

        self._ensure_worker()
        self._queue.put(text)

    def stop(self) -> None:
        if self._worker and self._worker.is_alive():
            self._queue.put(None)
            self._worker.join(timeout=2)
        self._worker = None

    def _ensure_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._worker = Thread(target=self._worker_loop, name="orb-tts", daemon=True)
        self._worker.start()

    def _worker_loop(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                break
            self._speak_blocking(text)

    def _speak_blocking(self, text: str) -> None:
        try:
            with self._engine_lock:
                engine = self._get_engine()
                engine.say(text)
                engine.runAndWait()
        except Exception as exc:
            logger.error("TTS failed: %s", exc)

    def _get_engine(self) -> Any:
        if self._engine is not None:
            return self._engine

        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", self.settings.tts_rate)
        engine.setProperty("volume", self.settings.tts_volume)
        self._engine = engine
        return engine


_DEFAULT_TTS = TextToSpeech()
atexit.register(_DEFAULT_TTS.stop)


def speak(text: str, block: bool | None = None) -> None:
    _DEFAULT_TTS.speak(text, block=block)
