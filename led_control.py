from config import (
    TEST_MODE,
    LED_ENABLED,
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_BRIGHTNESS,
    LED_INVERT,
)

_strip = None
Color = None


def init_led():
    global _strip, Color

    if TEST_MODE or not LED_ENABLED:
        print("[LED] Test mode active - no real LED initialization")
        return True

    try:
        from rpi_ws281x import PixelStrip, Color as WsColor

        Color = WsColor
        _strip = PixelStrip(
            LED_COUNT,
            LED_PIN,
            LED_FREQ_HZ,
            LED_DMA,
            LED_INVERT,
            LED_BRIGHTNESS,
        )
        _strip.begin()
        print("[LED] Real LED ring initialized")
        return True

    except Exception as e:
        print(f"[LED] Initialization failed: {e}")
        return False


def _fill_color(r, g, b):
    if TEST_MODE or not LED_ENABLED or _strip is None or Color is None:
        return

    for i in range(_strip.numPixels()):
        _strip.setPixelColor(i, Color(r, g, b))
    _strip.show()


def show_startup_light():
    print("[LED] Startup animation")
    _fill_color(255, 180, 0)


def show_success_light():
    print("[LED] Green - Success")
    _fill_color(0, 255, 0)


def show_error_light():
    print("[LED] Red - Error")
    _fill_color(255, 0, 0)


def show_listening_light():
    print("[LED] Blue - Listening")
    _fill_color(0, 0, 255)


def show_processing_light():
    print("[LED] Purple - Processing")
    _fill_color(180, 0, 255)


def show_speaking_light():
    print("[LED] Cyan - Speaking")
    _fill_color(0, 255, 255)


def show_idle_light():
    print("[LED] Soft Blue - Idle")
    _fill_color(0, 80, 255)


def turn_off():
    print("[LED] Off")
    _fill_color(0, 0, 0)


if __name__ == "__main__":
    import time

    print("Testing led_control.py")
    init_led()

    show_startup_light()
    time.sleep(1)

    show_success_light()
    time.sleep(1)

    show_listening_light()
    time.sleep(1)

    show_processing_light()
    time.sleep(1)

    show_speaking_light()
    time.sleep(1)

    show_error_light()
    time.sleep(1)

    show_idle_light()
    time.sleep(1)

    turn_off()
