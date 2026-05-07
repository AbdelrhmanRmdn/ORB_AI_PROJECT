from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import time
from typing import Any

from camera import CameraSource
from config import Settings, SETTINGS
from logging_config import get_logger


logger = get_logger("yolo_detector")


@dataclass(frozen=True)
class PersonDetection:
    found: bool
    confidence: float = 0.0
    bbox: tuple[int, int, int, int] | None = None
    elapsed_ms: float = 0.0
    skipped: bool = False


class YOLOPersonDetector:
    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings
        self._model: Any | None = None
        self._frame_count = 0
        self._last_detection = PersonDetection(False)

    def detect_person(self, frame: Any | None) -> PersonDetection:
        if self.settings.test_mode or not self.settings.yolo_enabled:
            detection = PersonDetection(found=self.settings.mock_person_detected, confidence=1.0)
            self._last_detection = detection
            return detection

        self._frame_count += 1
        if self._frame_count % max(1, self.settings.yolo_frame_skip) != 0:
            return PersonDetection(
                found=self._last_detection.found,
                confidence=self._last_detection.confidence,
                bbox=self._last_detection.bbox,
                skipped=True,
            )

        model = self._get_model()
        started = time.perf_counter()
        results = model.predict(
            frame,
            imgsz=self.settings.yolo_image_size,
            conf=self.settings.yolo_confidence,
            classes=[0],
            device=self.settings.yolo_device,
            verbose=False,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000

        best = PersonDetection(False, elapsed_ms=elapsed_ms)
        if results:
            boxes = getattr(results[0], "boxes", None)
            if boxes is not None and len(boxes) > 0:
                confidences = boxes.conf.cpu().numpy()
                index = int(confidences.argmax())
                confidence = float(confidences[index])
                xyxy = boxes.xyxy.cpu().numpy()[index]
                bbox = tuple(int(value) for value in xyxy)
                best = PersonDetection(True, confidence, bbox, elapsed_ms)

        logger.debug("YOLO person detection: %s", best)
        self._last_detection = best
        return best

    def wait_for_person(
        self,
        camera: CameraSource | None = None,
        timeout_seconds: float | None = None,
    ) -> tuple[Any | None, PersonDetection]:
        timeout = self.settings.person_wait_timeout_seconds if timeout_seconds is None else timeout_seconds
        owns_camera = camera is None
        camera = camera or CameraSource(self.settings)
        deadline = time.time() + timeout

        if owns_camera:
            camera.open()

        try:
            while time.time() <= deadline:
                frame_result = camera.read_frame()
                if not frame_result.ok:
                    logger.warning("Camera read failed: %s", frame_result.error)
                    time.sleep(0.2)
                    continue

                detection = self.detect_person(frame_result.frame)
                if detection.found:
                    return frame_result.frame, detection
                time.sleep(0.05)
            return None, PersonDetection(False)
        finally:
            if owns_camera:
                camera.release()

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        from ultralytics import YOLO

        self.settings.models_dir.mkdir(parents=True, exist_ok=True)
        configured = Path(self.settings.yolo_model)
        local_model = self.settings.models_dir / "yolov8n.pt"

        if configured.exists():
            source = str(configured)
        elif local_model.exists():
            source = str(local_model)
        else:
            source = self.settings.yolo_model

        logger.info("Loading YOLO model from %s", source)
        self._model = YOLO(source)

        downloaded = Path("yolov8n.pt")
        if not local_model.exists() and downloaded.exists():
            try:
                shutil.copy2(downloaded, local_model)
                logger.info("Cached YOLO model at %s", local_model)
            except Exception as exc:
                logger.warning("Could not cache YOLO model: %s", exc)

        return self._model
