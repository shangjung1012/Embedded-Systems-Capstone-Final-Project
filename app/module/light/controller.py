from __future__ import annotations

import os
import sys

try:
    from rpi_ws281x import Color, PixelStrip
except ImportError:
    Color = None      # type: ignore[assignment]
    PixelStrip = None  # type: ignore[assignment]

LED_COUNT = 120
_LED_PIN = 18
_LED_FREQ_HZ = 800000
_LED_DMA = 10
_LED_BRIGHTNESS = 50
_LED_INVERT = False
_LED_CHANNEL = 0


class LightController:
    def __init__(self) -> None:
        if PixelStrip is None:
            print("[light] rpi_ws281x is not installed; LED output is disabled", file=sys.stderr)
            self.strip = None
            return

        if hasattr(os, "geteuid") and os.geteuid() != 0:
            print("[light] rpi_ws281x requires root access; LED output is disabled", file=sys.stderr)
            self.strip = None
            return

        try:
            self.strip = PixelStrip(
                LED_COUNT, _LED_PIN, _LED_FREQ_HZ, _LED_DMA,
                _LED_INVERT, _LED_BRIGHTNESS, _LED_CHANNEL,
            )
            self.strip.begin()
        except Exception as error:
            print(f"[light] LED strip unavailable, using no-op: {error}", file=sys.stderr)
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
            self._set_all(
                int(red * brightness),
                int(green * brightness),
                int(blue * brightness),
            )

    def off(self) -> None:
        self.apply({"rgb": [0, 0, 0], "brightness": 0.0})

    def _set_all(self, red: int, green: int, blue: int) -> None:
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(red, green, blue))
        self.strip.show()


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
