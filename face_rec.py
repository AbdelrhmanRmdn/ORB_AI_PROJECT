from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from camera import CameraSource
from config import Settings, SETTINGS
from database.database_manager import DatabaseManager
from logging_config import get_logger


logger = get_logger("face_rec")
SUPPORTED_FACE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class FaceIdentity:
    name: str | None
    authorized: bool
    confidence: float
    distance: float | None = None
    reason: str = ""


class FaceRecognizer:
    def __init__(
        self,
        settings: Settings = SETTINGS,
        database: DatabaseManager | None = None,
    ) -> None:
        self.settings = settings
        self.database = database
        self._known_names: list[str] = []
        self._known_encodings: list[Any] = []
        self._database_authorized_names: set[str] | None = None
        self._loaded = False

    def load_known_faces(self) -> int:
        if self._loaded:
            return len(self._known_encodings)

        self._loaded = True
        self._known_names.clear()
        self._known_encodings.clear()

        if self.settings.test_mode or not self.settings.face_recognition_enabled:
            self._known_names.append(self.settings.mock_user)
            self._known_encodings.append(None)
            logger.info("Face recognition mock user loaded: %s", self.settings.mock_user)
            return 1

        try:
            import face_recognition
        except Exception as exc:
            logger.error("face_recognition dependency unavailable: %s", exc)
            return 0

        self._sync_authorized_users_from_database()
        if self.database and self.settings.database_sync_face_metadata:
            synced = self.database.sync_local_face_metadata(self.settings.faces_dir)
            logger.info("Synced %s local face metadata record(s) to Supabase", synced)

        self.settings.faces_dir.mkdir(parents=True, exist_ok=True)
        image_paths = [
            path
            for path in self.settings.faces_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_FACE_EXTENSIONS
        ]

        for image_path in image_paths:
            try:
                image = face_recognition.load_image_file(str(image_path))
                locations = face_recognition.face_locations(
                    image,
                    model=self.settings.face_model,
                )
                encodings = face_recognition.face_encodings(image, locations)
                if not encodings:
                    logger.warning("No face encoding found in %s", image_path)
                    continue
                self._known_names.append(self._name_from_path(image_path))
                self._known_encodings.append(encodings[0])
            except Exception as exc:
                logger.warning("Could not load face image %s: %s", image_path, exc)

        logger.info("Loaded %s known face encoding(s)", len(self._known_encodings))
        return len(self._known_encodings)

    def recognize(self, frame: Any | None = None) -> FaceIdentity:
        if self.settings.test_mode or not self.settings.face_recognition_enabled:
            user = self.settings.mock_user
            return FaceIdentity(user, self._is_authorized(user), 1.0, reason="mock")

        if not self._loaded:
            self.load_known_faces()

        if not self._known_encodings:
            return FaceIdentity(None, False, 0.0, reason="no_known_faces")

        if frame is None:
            frame = self._capture_single_frame()
            if frame is None:
                return FaceIdentity(None, False, 0.0, reason="camera_unavailable")

        try:
            import cv2
            import face_recognition
            import numpy as np
        except Exception as exc:
            logger.error("Face recognition runtime dependencies unavailable: %s", exc)
            return FaceIdentity(None, False, 0.0, reason="dependency_error")

        scale = max(0.1, min(1.0, self.settings.face_scale))
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb_frame = small_frame[:, :, ::-1]
        locations = face_recognition.face_locations(
            rgb_frame,
            model=self.settings.face_model,
        )
        encodings = face_recognition.face_encodings(rgb_frame, locations)

        if not encodings:
            return FaceIdentity(None, False, 0.0, reason="no_face_detected")

        face_encoding = encodings[0]
        distances = face_recognition.face_distance(self._known_encodings, face_encoding)
        if len(distances) == 0:
            return FaceIdentity(None, False, 0.0, reason="no_known_faces")

        best_index = int(np.argmin(distances))
        best_distance = float(distances[best_index])
        if best_distance > self.settings.face_tolerance:
            return FaceIdentity(
                None,
                False,
                max(0.0, 1.0 - best_distance),
                distance=best_distance,
                reason="unknown_face",
            )

        name = self._known_names[best_index]
        return FaceIdentity(
            name,
            self._is_authorized(name),
            max(0.0, 1.0 - best_distance),
            distance=best_distance,
            reason="recognized",
        )

    def _capture_single_frame(self) -> Any | None:
        with CameraSource(self.settings) as camera:
            frame_result = camera.read_frame()
            if frame_result.ok:
                return frame_result.frame
        return None

    def _is_authorized(self, name: str | None) -> bool:
        if not name:
            return False
        if not self.settings.require_authorization:
            return True
        if self._database_authorized_names:
            return name.lower() in self._database_authorized_names
        authorized = {user.lower() for user in self.settings.authorized_users}
        return name.lower() in authorized

    def _sync_authorized_users_from_database(self) -> None:
        if self.database is None:
            return
        users = self.database.get_authorized_users()
        if not users:
            return
        self._database_authorized_names = {user.name.lower() for user in users}
        logger.info(
            "Loaded %s authorized user(s) from Supabase",
            len(self._database_authorized_names),
        )

    def _name_from_path(self, path: Path) -> str:
        if path.parent != self.settings.faces_dir:
            raw_name = path.parent.name
        else:
            raw_name = path.stem
        raw_name = re.sub(r"[_\-\s]*\d+$", "", raw_name)
        return raw_name.replace("_", " ").strip().title()


_DEFAULT_RECOGNIZER: FaceRecognizer | None = None


def get_default_recognizer() -> FaceRecognizer:
    global _DEFAULT_RECOGNIZER
    if _DEFAULT_RECOGNIZER is None:
        _DEFAULT_RECOGNIZER = FaceRecognizer()
    return _DEFAULT_RECOGNIZER


def recognize_user(frame: Any | None = None) -> FaceIdentity:
    return get_default_recognizer().recognize(frame)


def identify_user(frame: Any | None = None) -> str | None:
    identity = recognize_user(frame)
    return identity.name if identity.authorized else None


if __name__ == "__main__":
    print("Testing face_rec.py")
    result = recognize_user()
    print(f"Detected user: {result.name}, authorized={result.authorized}, reason={result.reason}")
