from __future__ import annotations

import argparse
from dataclasses import dataclass
from dataclasses import replace
import importlib
from pathlib import Path
import traceback


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    message: str


class FinalSystemChecker:
    def __init__(
        self,
        real: bool = False,
        load_models: bool = False,
        strict: bool = False,
    ) -> None:
        self.real = real
        self.load_models = load_models
        self.strict = strict
        self.results: list[CheckResult] = []
        self.root = Path(__file__).resolve().parent

    def run(self) -> int:
        self._check_required_files()
        self._check_imports()
        self._check_dependencies()
        self._check_config()
        self._check_ai_flow()
        self._check_camera()
        self._check_audio()
        self._check_face_database()
        self._check_yolo()
        self._check_whisper()
        self._check_supabase()
        self._print_report()
        return 0 if self._ready() else 1

    def _add(self, name: str, status: str, message: str) -> None:
        self.results.append(CheckResult(name, status, message))

    def _ok(self, name: str, message: str) -> None:
        self._add(name, "OK", message)

    def _warn(self, name: str, message: str) -> None:
        self._add(name, "WARN", message)

    def _fail(self, name: str, message: str) -> None:
        self._add(name, "FAIL", message)

    def _check_required_files(self) -> None:
        required = [
            "main.py",
            "simulation_mode.py",
            "final_system_check.py",
            "requirements.txt",
            ".env.example",
            "README.md",
            "database/schema.sql",
            "database/database_manager.py",
            "data/faces/.gitkeep",
            "data/models/.gitkeep",
            "logs/.gitkeep",
        ]
        missing = [path for path in required if not (self.root / path).exists()]
        if missing:
            self._fail("Project files", f"Missing: {', '.join(missing)}")
        else:
            self._ok("Project files", "Required deployment files are present")

    def _check_imports(self) -> None:
        modules = [
            "app",
            "assistant_brain",
            "camera",
            "config",
            "database.database_manager",
            "database.models",
            "database.queries",
            "database.supabase_client",
            "face_rec",
            "final_system_check",
            "intent_handler",
            "led_control",
            "logging_config",
            "main",
            "orb_pipeline",
            "response_generator",
            "simulation_mode",
            "speech_to_text",
            "system_status",
            "text_to_speech",
            "voice_assistant",
            "yolo_detector",
        ]
        failed: list[str] = []
        for module_name in modules:
            try:
                importlib.import_module(module_name)
            except Exception as exc:
                failed.append(f"{module_name}: {exc}")
        if failed:
            self._fail("Python imports", "; ".join(failed))
        else:
            self._ok("Python imports", "All project modules import successfully")

    def _check_dependencies(self) -> None:
        dependencies = {
            "numpy": self.real,
            "cv2": self.real,
            "face_recognition": self.real,
            "faster_whisper": self.real,
            "pyttsx3": self.real,
            "sounddevice": self.real,
            "supabase": False,
            "ultralytics": self.real,
        }
        missing_required: list[str] = []
        missing_optional: list[str] = []
        for module_name, required in dependencies.items():
            try:
                importlib.import_module(module_name)
            except Exception:
                if required:
                    missing_required.append(module_name)
                else:
                    missing_optional.append(module_name)

        if missing_required:
            self._fail("Dependencies", f"Missing required real-mode packages: {missing_required}")
        elif missing_optional:
            self._warn("Dependencies", f"Optional packages not installed here: {missing_optional}")
        else:
            self._ok("Dependencies", "Runtime dependency imports passed")

    def _check_config(self) -> None:
        from config import load_settings

        settings = load_settings()
        path_fields = [
            settings.data_dir,
            settings.faces_dir,
            settings.models_dir,
            settings.recordings_dir,
            settings.log_dir,
        ]
        missing_dirs = [str(path) for path in path_fields if not path.exists()]
        if missing_dirs:
            self._fail("Configuration", f"Missing configured directories: {missing_dirs}")
            return

        if settings.project_root != self.root:
            self._warn("Configuration", f"Project root is {settings.project_root}")
        else:
            self._ok("Configuration", "Settings loaded and runtime directories exist")

    def _check_ai_flow(self) -> None:
        from response_generator import ResponseGenerator

        response = ResponseGenerator().generate("hello", current_user="Boudy")
        if response.intent.name == "greeting" and "Boudy" in response.text:
            self._ok("AI flow", "Intent classification and response generation work")
        else:
            self._fail("AI flow", f"Unexpected response: {response}")

    def _check_camera(self) -> None:
        from camera import CameraSource
        from config import load_settings

        settings = replace(load_settings(), test_mode=not self.real)
        try:
            with CameraSource(settings) as camera:
                frame = camera.read_frame()
        except Exception as exc:
            self._fail("Camera", str(exc))
            return

        if frame.ok and frame.frame is not None:
            mode = "real" if self.real else "mock"
            self._ok("Camera", f"{mode} camera returned frame shape {frame.frame.shape}")
        else:
            self._fail("Camera", frame.error or "No frame returned")

    def _check_audio(self) -> None:
        from config import load_settings
        from speech_to_text import SpeechToText
        from text_to_speech import TextToSpeech

        settings = replace(load_settings(), test_mode=True)
        stt = SpeechToText(settings, mock_command="system status")
        tts = TextToSpeech(settings)
        command = stt.listen()
        tts.speak("Audio simulation check", block=True)
        if command == "system status":
            self._ok("Audio", "Mock STT and mock TTS path works")
        else:
            self._fail("Audio", f"Mock STT returned {command!r}")

    def _check_face_database(self) -> None:
        from config import load_settings
        from face_rec import FaceRecognizer

        settings = replace(load_settings(), test_mode=not self.real)
        recognizer = FaceRecognizer(settings)
        loaded = recognizer.load_known_faces()
        if self.real and loaded == 0:
            self._warn("Face database", "No known face encodings loaded from data/faces")
        else:
            self._ok("Face database", f"Loaded {loaded} known face profile(s)")

    def _check_yolo(self) -> None:
        from config import load_settings
        from yolo_detector import YOLOPersonDetector

        settings = replace(load_settings(), test_mode=not self.real)
        detector = YOLOPersonDetector(settings)
        if not self.real:
            detection = detector.detect_person(None)
            self._ok("YOLO", f"Mock person detection found={detection.found}")
            return

        if not self.load_models:
            self._warn("YOLO", "Real model load skipped; rerun with --load-models on the Pi")
            return

        try:
            detector._get_model()
        except Exception as exc:
            self._fail("YOLO", f"Could not load YOLO model: {exc}")
            return
        self._ok("YOLO", "YOLO model loaded")

    def _check_whisper(self) -> None:
        from config import load_settings
        from speech_to_text import SpeechToText

        settings = replace(load_settings(), test_mode=not self.real)
        stt = SpeechToText(settings, mock_command="hello")
        if not self.real:
            self._ok("Whisper", "Mock STT path works; real load skipped")
            return

        if not self.load_models:
            self._warn("Whisper", "Real model load skipped; rerun with --load-models on the Pi")
            return

        try:
            stt._get_model()
        except Exception as exc:
            self._fail("Whisper", f"Could not load faster-whisper model: {exc}")
            return
        self._ok("Whisper", "faster-whisper model loaded")

    def _check_supabase(self) -> None:
        from config import load_settings
        from database.database_manager import DatabaseManager

        health = DatabaseManager(load_settings()).health_check()
        if health.reachable:
            self._ok("Supabase", health.message)
        elif self.strict:
            self._fail("Supabase", health.message)
        else:
            self._warn("Supabase", f"{health.message}; offline mode remains usable")

    def _ready(self) -> bool:
        statuses = {result.status for result in self.results}
        if "FAIL" in statuses:
            return False
        if self.strict and "WARN" in statuses:
            return False
        return True

    def _print_report(self) -> None:
        print("\n=== ORB AI Assistant Final System Check ===")
        for result in self.results:
            print(f"[{result.status}] {result.name}: {result.message}")

        if self._ready():
            if self.real and self.load_models and not any(
                result.status == "WARN" for result in self.results
            ):
                print("\nFINAL STATUS: READY FOR RASPBERRY PI")
            else:
                print("\nFINAL STATUS: READY FOR SIMULATION")
                print("Run with --real --load-models --strict on the Raspberry Pi for hardware release sign-off.")
        else:
            print("\nFINAL STATUS: NOT READY")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run final ORB deployment checks.")
    parser.add_argument("--real", action="store_true", help="Check real hardware dependencies")
    parser.add_argument(
        "--load-models",
        action="store_true",
        help="Actually load YOLO and Whisper models; may download on first run",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as release blockers",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    checker = FinalSystemChecker(
        real=args.real,
        load_models=args.load_models,
        strict=args.strict,
    )
    try:
        raise SystemExit(checker.run())
    except KeyboardInterrupt:
        print("\n[FAIL] Interrupted by user")
        raise SystemExit(130)
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
