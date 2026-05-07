from __future__ import annotations

from config import SETTINGS
from logging_config import get_logger


logger = get_logger("led_control")
_strip = None
Color = None


def init_led() -> bool:
    global _strip, Color

    if SETTINGS.test_mode or not SETTINGS.led_enabled:
        logger.info("LED mock mode active")
        return True

    try:
        from rpi_ws281x import PixelStrip, Color as WsColor

        Color = WsColor
        _strip = PixelStrip(
            SETTINGS.led_count,
            SETTINGS.led_pin,
            SETTINGS.led_freq_hz,
            SETTINGS.led_dma,
            SETTINGS.led_invert,
            SETTINGS.led_brightness,
        )
        _strip.begin()
        logger.info("LED ring initialized")
        return True
    except Exception as exc:
        logger.error("LED initialization failed: %s", exc)
        return False


def _fill_color(r: int, g: int, b: int) -> None:
    if SETTINGS.test_mode or not SETTINGS.led_enabled or _strip is None or Color is None:
        return

    for index in range(_strip.numPixels()):
        _strip.setPixelColor(index, Color(r, g, b))
    _strip.show()


def show_startup_light() -> None:
    logger.info("LED startup")
    _fill_color(255, 180, 0)


def show_success_light() -> None:
    logger.info("LED success")
    _fill_color(0, 255, 0)


def show_error_light() -> None:
    logger.info("LED error")
    _fill_color(255, 0, 0)


def show_listening_light() -> None:
    logger.info("LED listening")
    _fill_color(0, 0, 255)


def show_processing_light() -> None:
    logger.info("LED processing")
    _fill_color(180, 0, 255)


def show_speaking_light() -> None:
    logger.info("LED speaking")
    _fill_color(0, 255, 255)


def show_idle_light() -> None:
    logger.info("LED idle")
    _fill_color(0, 80, 255)


def turn_off() -> None:
    logger.info("LED off")
    _fill_color(0, 0, 0)


if __name__ == "__main__":
    import time

    print("Testing led_control.py")
    init_led()
    for show in (
        show_startup_light,
        show_success_light,
        show_listening_light,
        show_processing_light,
        show_speaking_light,
        show_error_light,
        show_idle_light,
    ):
        show()
        time.sleep(1)
    turn_off()
