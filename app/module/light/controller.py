from __future__ import annotations

import sys

try:
    from rpi_ws281x import Color, PixelStrip
except ImportError:
    Color = None      # type: ignore[assignment]
    PixelStrip = None  # type: ignore[assignment]

_LED_COUNT = 40
_LED_PIN = 18
_LED_FREQ_HZ = 800000
_LED_DMA = 10
_LED_INVERT = False
_LED_CHANNEL = 0


class LightController:
    def __init__(self) -> None:
        if PixelStrip is not None:
            try:
                self.strip = PixelStrip(
                    _LED_COUNT, _LED_PIN, _LED_FREQ_HZ, _LED_DMA,
                    _LED_INVERT, 255, _LED_CHANNEL,
                )
                self.strip.begin()
            except Exception as error:
                print(f"[light] LED strip unavailable, using no-op: {error}", file=sys.stderr)
                self.strip = None
        else:
            self.strip = None

    def apply(self, config: dict[str, object]) -> None:
        rgb = config.get("rgb", [0, 0, 0])
        brightness = float(config.get("brightness", 0.0))
        if not isinstance(rgb, list) or len(rgb) != 3:
            rgb = [0, 0, 0]
        red, green, blue = (_clamp(int(value), 0, 255) for value in rgb)
        brightness = max(0.0, min(1.0, brightness))
        print(f"[light] rgb=({red},{green},{blue}) brightness={brightness:.2f}")
        if self.strip is not None:
            self.strip.setBrightness(int(brightness * 255))
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(red, green, blue))
            self.strip.show()

    def off(self) -> None:
        self.apply({"rgb": [0, 0, 0], "brightness": 0.0})


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))

