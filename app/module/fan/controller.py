from __future__ import annotations

from app.gpio import GpioPins, create_output_device


class FanController:
    def __init__(self) -> None:
        self.ina = create_output_device(GpioPins.FAN_INA)
        self.inb = create_output_device(GpioPins.FAN_INB)

    def apply(self, config: dict[str, object]) -> None:
        speed = int(config.get("speed", 0))
        speed = _clamp(speed)
        if speed > 0:
            self._on(speed)
        else:
            self.off()

    def off(self) -> None:
        print("[fan] OFF")
        self.ina.off()
        self.inb.off()

    def _on(self, speed: int) -> None:
        print(f"[fan] ON speed={speed}")
        self.ina.off()
        self.inb.on()


def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))
