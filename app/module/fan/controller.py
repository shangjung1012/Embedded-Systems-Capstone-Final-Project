from __future__ import annotations

try:
    from gpiozero import OutputDevice
except ImportError:  # Allows development on machines without gpiozero.
    OutputDevice = None  # type: ignore[assignment]


FAN_INA_GPIO = 22  # GPIO22 = physical pin 15
FAN_INB_GPIO = 27  # GPIO27 = physical pin 13


class FanController:
    def __init__(self) -> None:
        if OutputDevice is None:
            self.ina = None
            self.inb = None
        else:
            self.ina = OutputDevice(FAN_INA_GPIO)
            self.inb = OutputDevice(FAN_INB_GPIO)

    def apply(self, config: dict[str, object]) -> None:
        speed = int(config.get("speed", 0))
        speed = _clamp(speed)
        if speed > 0:
            self._on(speed)
        else:
            self.off()

    def off(self) -> None:
        print("[fan] OFF")
        if self.ina is not None and self.inb is not None:
            self.ina.off()
            self.inb.off()

    def _on(self, speed: int) -> None:
        print(f"[fan] ON speed={speed}")
        if self.ina is not None and self.inb is not None:
            self.ina.off()
            self.inb.on()


def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))
