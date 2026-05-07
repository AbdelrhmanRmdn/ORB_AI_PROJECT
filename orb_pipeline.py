from __future__ import annotations

from dataclasses import dataclass
import time

from database.database_manager import DatabaseManager
import led_control
from config import Settings, SETTINGS
from face_rec import FaceIdentity, FaceRecognizer
from logging_config import configure_logging, get_logger
from response_generator import GeneratedResponse, ResponseGenerator
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech
from yolo_detector import PersonDetection, YOLOPersonDetector


logger = get_logger("pipeline")


@dataclass(frozen=True)
class CycleResult:
    person_detected: bool
    identity: FaceIdentity | None
    command: str | None
    response: GeneratedResponse | None
    shutdown_requested: bool = False


class ORBAssistant:
    def __init__(
        self,
        settings: Settings = SETTINGS,
        detector: YOLOPersonDetector | None = None,
        recognizer: FaceRecognizer | None = None,
        stt: SpeechToText | None = None,
        tts: TextToSpeech | None = None,
        responses: ResponseGenerator | None = None,
        database: DatabaseManager | None = None,
        mock_command: str | None = None,
    ) -> None:
        self.settings = settings
        self.database = database or DatabaseManager(settings)
        self.detector = detector or YOLOPersonDetector(settings)
        self.recognizer = recognizer or FaceRecognizer(settings, database=self.database)
        self.stt = stt or SpeechToText(settings, mock_command=mock_command)
        self.tts = tts or TextToSpeech(settings)
        self.responses = responses or ResponseGenerator(settings=settings)
        self._initialized = False

    def setup(self) -> None:
        if self._initialized:
            return
        configure_logging(self.settings)
        logger.info("ORB AI System starting")
        health = self.database.health_check()
        logger.info("Database status: %s", health.message)
        self.database.log_event("startup", "ORB AI System starting")
        led_control.init_led()
        led_control.show_startup_light()
        self.recognizer.load_known_faces()
        self._initialized = True

    def run(self, max_cycles: int | None = None) -> None:
        self.setup()
        completed = 0
        shutdown = False

        while not shutdown:
            result = self.run_once()
            completed += 1
            shutdown = result.shutdown_requested

            if max_cycles is not None and completed >= max_cycles:
                break

            time.sleep(self.settings.conversation_cooldown_seconds)

        self.shutdown()

    def run_once(self) -> CycleResult:
        self.setup()
        led_control.show_idle_light()
        frame, detection = self.detector.wait_for_person()
        if not detection.found:
            logger.info("No person detected before timeout")
            return CycleResult(False, None, None, None)

        logger.info(
            "Person detected with confidence %.2f and bbox %s",
            detection.confidence,
            detection.bbox,
        )
        led_control.show_processing_light()
        identity = self.recognizer.recognize(frame)
        if not identity.authorized:
            return self._handle_unauthorized(identity)

        led_control.show_success_light()
        self.tts.speak(f"Hello {identity.name}, I am online and ready.")

        command = self._listen_with_retries()
        if not command:
            self.tts.speak("I am having trouble hearing you.")
            self.database.log_event("voice_timeout", "No command recognized")
            return CycleResult(True, identity, None, None)

        logger.info("Command received: %s", command)
        led_control.show_processing_light()
        response = self.responses.generate(command, current_user=identity.name)
        logger.info("Intent=%s Response=%s", response.intent.name, response.text)

        led_control.show_speaking_light()
        self.tts.speak(response.text)
        self.database.log_interaction(identity.name, command, response.text)

        return CycleResult(
            True,
            identity,
            command,
            response,
            shutdown_requested=response.should_shutdown,
        )

    def _listen_with_retries(self) -> str | None:
        led_control.show_listening_light()
        for attempt in range(1, self.settings.max_voice_retries + 1):
            started = time.perf_counter()
            command = self.stt.listen()
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info("Listen attempt %s finished in %.0f ms", attempt, elapsed_ms)
            if command:
                return command
        return None

    def _handle_unauthorized(self, identity: FaceIdentity) -> CycleResult:
        led_control.show_error_light()
        if identity.name:
            message = f"{identity.name} is recognized but not authorized."
        elif identity.reason == "no_known_faces":
            message = "No authorized face profiles are installed."
        else:
            message = "Face not recognized."
        logger.warning("Unauthorized access: %s", identity)
        self.database.log_event("unauthorized_face", message)
        self.tts.speak(message)
        return CycleResult(True, identity, None, None)

    def shutdown(self) -> None:
        logger.info("ORB AI System shutting down")
        self.database.log_event("shutdown", "ORB AI System shutting down")
        led_control.turn_off()
        self.tts.stop()


def run_once(settings: Settings = SETTINGS, mock_command: str | None = None) -> CycleResult:
    return ORBAssistant(settings=settings, mock_command=mock_command).run_once()
