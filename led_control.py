from config import LED_ENABLED, LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_BRIGHTNESS, LED_INVERT


_strip = None


def init_led():
	global _strip

	if not LED_ENABLED:
		return

	try:
		from rpi_ws281x import PixelStrip, Color
	except Exception as exc:
		print(f"[LED] LED support unavailable: {exc}")
		_strip = None
		return

	_ = Color
	_strip = PixelStrip(
		LED_COUNT,
		LED_PIN,
		LED_FREQ_HZ,
		LED_DMA,
		LED_INVERT,
		LED_BRIGHTNESS,
	)
	_strip.begin()


def _clear():
	if not LED_ENABLED or _strip is None:
		return

	for index in range(_strip.numPixels()):
		_strip.setPixelColor(index, 0)
	_strip.show()


def _fill(red, green, blue):
	if not LED_ENABLED or _strip is None:
		return

	try:
		from rpi_ws281x import Color
	except Exception:
		return

	for index in range(_strip.numPixels()):
		_strip.setPixelColor(index, Color(red, green, blue))
	_strip.show()


def show_startup_light():
	_fill(0, 0, 40)


def show_success_light():
	_fill(0, 40, 0)


def show_error_light():
	_fill(40, 0, 0)


def show_listening_light():
	_fill(0, 30, 40)


def show_processing_light():
	_fill(40, 20, 0)


def show_speaking_light():
	_fill(25, 0, 35)


def show_idle_light():
	_clear()


def turn_off():
	_clear()
