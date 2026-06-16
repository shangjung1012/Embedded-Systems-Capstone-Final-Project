from __future__ import annotations

from app.gpio import GpioPins, create_output_device


class FanController:
    def __init__(self) -> None:
        self.ina = create_output_device(GpioPins.FAN_INA)
        self.inb = create_output_device(GpioPins.FAN_INB)

    def apply(self, config: dict[str, object]) -> None:
        if bool(config.get("enabled", False)):
            self._on()
        else:
            self.off()

    def off(self) -> None:
        print("[fan] OFF")
        self.ina.off()
        self.inb.off()

    def _on(self) -> None:
        print("[fan] ON")
        self.ina.off()
        self.inb.on()
