from __future__ import annotations

import time

from app.gpio import GpioPins

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None  # type: ignore[assignment]


class MistController:
    def __init__(self) -> None:
        self.pin = GpioPins.MIST.gpio
        if GPIO is None:
            self.available = False
            return

        self.available = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.HIGH)

    def apply(self, config: dict[str, object]) -> None:
        enabled = bool(config.get("enabled", False))
        print(f"[mist] enabled={str(enabled).lower()}")
        if enabled:
            self._on()
        else:
            self._off()

    def off(self) -> None:
        self.apply({"enabled": False})

    def _on(self) -> None:
        if self.available:
            GPIO.output(self.pin, GPIO.LOW)  # GPIO LOW → 霧化開啟

    def _off(self) -> None:
        if self.available:
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.1)
