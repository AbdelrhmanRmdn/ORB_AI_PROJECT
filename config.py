from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_FACES_DIR = DEFAULT_DATA_DIR / "faces"
DEFAULT_MODELS_DIR = DEFAULT_DATA_DIR / "models"
DEFAULT_RECORDINGS_DIR = DEFAULT_DATA_DIR / "recordings"
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"


def _load_env_file() -> None:
    """Load .env without making python-dotenv mandatory for mock startup."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
        return
    except Exception:
        pass

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_optional_int(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if value is None or value.strip().lower() in {"", "none", "null", "auto"}:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_path(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default))).expanduser().resolve()


def _env_tuple(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if not raw:
        return default
    values = tuple(part.strip() for part in raw.split(",") if part.strip())
    return values or default


_load_env_file()


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DEFAULT_DATA_DIR
    faces_dir: Path = DEFAULT_FACES_DIR
    models_dir: Path = DEFAULT_MODELS_DIR
    recordings_dir: Path = DEFAULT_RECORDINGS_DIR
    log_dir: Path = DEFAULT_LOG_DIR

    test_mode: bool = True
    log_level: str = "INFO"
    non_interactive: bool = False
    loop_once: bool = False
    mock_command: str | None = None
    mock_user: str = "Karim"
    mock_person_detected: bool = True

    require_authorization: bool = True
    authorized_users: tuple[str, ...] = ("Karim", "Admin")

    database_enabled: bool = True
    database_sync_users: bool = True
    database_sync_face_metadata: bool = False
    database_log_commands: bool = True
    database_log_events: bool = True

    camera_enabled: bool = True
    camera_index: int = 0
    camera_width: int = 320
    camera_height: int = 240
    camera_fps: int = 15
    camera_warmup_seconds: float = 0.2

    yolo_enabled: bool = True
    yolo_model: str = "yolov8n.pt"
    yolo_confidence: float = 0.45
    yolo_image_size: int = 320
    yolo_frame_skip: int = 5
    yolo_device: str = "cpu"
    person_wait_timeout_seconds: float = 20.0

    face_recognition_enabled: bool = True
    face_tolerance: float = 0.52
    face_scale: float = 0.25
    face_model: str = "hog"

    voice_enabled: bool = True
    listen_timeout: float = 5.0
    phrase_time_limit: float = 7.0
    max_voice_retries: int = 3
    voice_language: str = "en"

    whisper_model_size: str = "tiny"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_cpu_threads: int = 2
    microphone_sample_rate: int = 16000
    microphone_channels: int = 1
    microphone_device_index: int | None = None

    tts_enabled: bool = True
    tts_rate: int = 160
    tts_volume: float = 1.0
    tts_async: bool = True

    led_enabled: bool = True
    led_count: int = 16
    led_pin: int = 18
    led_freq_hz: int = 800000
    led_dma: int = 10
    led_brightness: int = 80
    led_invert: bool = False

    conversation_cooldown_seconds: float = 1.0


def load_settings() -> Settings:
    _load_env_file()
    settings = Settings(
        project_root=PROJECT_ROOT,
        data_dir=_env_path("ORB_DATA_DIR", DEFAULT_DATA_DIR),
        faces_dir=_env_path("ORB_FACES_DIR", DEFAULT_FACES_DIR),
        models_dir=_env_path("ORB_MODELS_DIR", DEFAULT_MODELS_DIR),
        recordings_dir=_env_path("ORB_RECORDINGS_DIR", DEFAULT_RECORDINGS_DIR),
        log_dir=_env_path("ORB_LOG_DIR", DEFAULT_LOG_DIR),
        test_mode=_env_bool("ORB_TEST_MODE", True),
        log_level=os.getenv("ORB_LOG_LEVEL", "INFO"),
        non_interactive=_env_bool("ORB_NONINTERACTIVE", False),
        loop_once=_env_bool("ORB_ONCE", False),
        mock_command=os.getenv("ORB_MOCK_COMMAND"),
        mock_user=os.getenv("ORB_MOCK_USER", "Karim"),
        mock_person_detected=_env_bool("ORB_MOCK_PERSON_DETECTED", True),
        require_authorization=_env_bool("ORB_REQUIRE_AUTHORIZATION", True),
        authorized_users=_env_tuple("ORB_AUTHORIZED_USERS", ("Karim", "Admin")),
        database_enabled=_env_bool("ORB_DATABASE_ENABLED", True),
        database_sync_users=_env_bool("ORB_DATABASE_SYNC_USERS", True),
        database_sync_face_metadata=_env_bool(
            "ORB_DATABASE_SYNC_FACE_METADATA", False
        ),
        database_log_commands=_env_bool("ORB_DATABASE_LOG_COMMANDS", True),
        database_log_events=_env_bool("ORB_DATABASE_LOG_EVENTS", True),
        camera_enabled=_env_bool("ORB_CAMERA_ENABLED", True),
        camera_index=_env_int("ORB_CAMERA_INDEX", 0),
        camera_width=_env_int("ORB_CAMERA_WIDTH", 320),
        camera_height=_env_int("ORB_CAMERA_HEIGHT", 240),
        camera_fps=_env_int("ORB_CAMERA_FPS", 15),
        camera_warmup_seconds=_env_float("ORB_CAMERA_WARMUP_SECONDS", 0.2),
        yolo_enabled=_env_bool("ORB_YOLO_ENABLED", True),
        yolo_model=os.getenv("ORB_YOLO_MODEL", "yolov8n.pt"),
        yolo_confidence=_env_float("ORB_YOLO_CONFIDENCE", 0.45),
        yolo_image_size=_env_int("ORB_YOLO_IMAGE_SIZE", 320),
        yolo_frame_skip=_env_int("ORB_YOLO_FRAME_SKIP", 5),
        yolo_device=os.getenv("ORB_YOLO_DEVICE", "cpu"),
        person_wait_timeout_seconds=_env_float("ORB_PERSON_WAIT_TIMEOUT", 20.0),
        face_recognition_enabled=_env_bool("ORB_FACE_RECOGNITION_ENABLED", True),
        face_tolerance=_env_float("ORB_FACE_TOLERANCE", 0.52),
        face_scale=_env_float("ORB_FACE_SCALE", 0.25),
        face_model=os.getenv("ORB_FACE_MODEL", "hog"),
        voice_enabled=_env_bool("ORB_VOICE_ENABLED", True),
        listen_timeout=_env_float("ORB_LISTEN_TIMEOUT", 5.0),
        phrase_time_limit=_env_float("ORB_PHRASE_TIME_LIMIT", 7.0),
        max_voice_retries=_env_int("ORB_MAX_VOICE_RETRIES", 3),
        voice_language=os.getenv("ORB_VOICE_LANGUAGE", "en"),
        whisper_model_size=os.getenv("ORB_WHISPER_MODEL_SIZE", "tiny"),
        whisper_device=os.getenv("ORB_WHISPER_DEVICE", "cpu"),
        whisper_compute_type=os.getenv("ORB_WHISPER_COMPUTE_TYPE", "int8"),
        whisper_cpu_threads=_env_int("ORB_WHISPER_CPU_THREADS", 2),
        microphone_sample_rate=_env_int("ORB_MIC_SAMPLE_RATE", 16000),
        microphone_channels=_env_int("ORB_MIC_CHANNELS", 1),
        microphone_device_index=_env_optional_int("ORB_MIC_DEVICE_INDEX", None),
        tts_enabled=_env_bool("ORB_TTS_ENABLED", True),
        tts_rate=_env_int("ORB_TTS_RATE", 160),
        tts_volume=_env_float("ORB_TTS_VOLUME", 1.0),
        tts_async=_env_bool("ORB_TTS_ASYNC", True),
        led_enabled=_env_bool("ORB_LED_ENABLED", True),
        led_count=_env_int("ORB_LED_COUNT", 16),
        led_pin=_env_int("ORB_LED_PIN", 18),
        led_freq_hz=_env_int("ORB_LED_FREQ_HZ", 800000),
        led_dma=_env_int("ORB_LED_DMA", 10),
        led_brightness=_env_int("ORB_LED_BRIGHTNESS", 80),
        led_invert=_env_bool("ORB_LED_INVERT", False),
        conversation_cooldown_seconds=_env_float("ORB_CONVERSATION_COOLDOWN", 1.0),
    )
    for path in (
        settings.data_dir,
        settings.faces_dir,
        settings.models_dir,
        settings.recordings_dir,
        settings.log_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return settings


SETTINGS = load_settings()

# Backwards-compatible constants for older modules.
TEST_MODE = SETTINGS.test_mode
LED_ENABLED = SETTINGS.led_enabled
FACE_RECOGNITION_ENABLED = SETTINGS.face_recognition_enabled
VOICE_ENABLED = SETTINGS.voice_enabled
VOICE_LANGUAGE = SETTINGS.voice_language
LISTEN_TIMEOUT = SETTINGS.listen_timeout
PHRASE_TIME_LIMIT = SETTINGS.phrase_time_limit
MAX_VOICE_RETRIES = SETTINGS.max_voice_retries
AUTHORIZED_USERS = list(SETTINGS.authorized_users)
LED_COUNT = SETTINGS.led_count
LED_PIN = SETTINGS.led_pin
LED_FREQ_HZ = SETTINGS.led_freq_hz
LED_DMA = SETTINGS.led_dma
LED_BRIGHTNESS = SETTINGS.led_brightness
LED_INVERT = SETTINGS.led_invert
MICROPHONE_DEVICE_INDEX = SETTINGS.microphone_device_index
