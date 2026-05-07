from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

from config import Settings, SETTINGS
from logging_config import get_logger


logger = get_logger("camera")


@dataclass(frozen=True)
class FrameResult:
    ok: bool
    frame: Any | None
    timestamp: float
    source: str
    error: str | None = None


@dataclass(frozen=True)
class MockFrame:
    height: int
    width: int
    channels: int = 3

    @property
    def shape(self) -> tuple[int, int, int]:
        return (self.height, self.width, self.channels)


class CameraSource:
    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings
        self._capture: Any | None = None

    def open(self) -> bool:
        if self.settings.test_mode or not self.settings.camera_enabled:
            logger.info("Camera mock mode active")
            return True

        import cv2

        self._capture = cv2.VideoCapture(self.settings.camera_index)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
        self._capture.set(cv2.CAP_PROP_FPS, self.settings.camera_fps)
        time.sleep(self.settings.camera_warmup_seconds)

        if not self._capture.isOpened():
            logger.error("Could not open camera index %s", self.settings.camera_index)
            self.release()
            return False
        return True

    def read_frame(self) -> FrameResult:
        if self.settings.test_mode or not self.settings.camera_enabled:
            return FrameResult(True, self._mock_frame(), time.time(), "mock")

        if self._capture is None and not self.open():
            return FrameResult(False, None, time.time(), "camera", "camera unavailable")

        ok, frame = self._capture.read()
        if not ok:
            return FrameResult(False, None, time.time(), "camera", "failed to read frame")
        return FrameResult(True, frame, time.time(), "camera")

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _mock_frame(self) -> Any:
        try:
            import numpy as np

            frame = np.zeros(
                (self.settings.camera_height, self.settings.camera_width, 3),
                dtype=np.uint8,
            )
            frame[:, :, 1] = 24
            return frame
        except Exception:
            return MockFrame(self.settings.camera_height, self.settings.camera_width)

    def __enter__(self) -> "CameraSource":
        self.open()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.release()


def camera_smoke_test(settings: Settings = SETTINGS) -> FrameResult:
    with CameraSource(settings) as camera:
        return camera.read_frame()
