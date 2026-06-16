from __future__ import annotations

from app.gpio import GpioPins, create_output_device


class VibratorController:
    def __init__(self) -> None:
        self.vibration = create_output_device(GpioPins.VIBRATION)

    def apply(self, config: dict[str, object]) -> None:
        if bool(config.get("enabled", False)):
            self._on()
        else:
            self.off()

    def off(self) -> None:
        print("[vibrator] OFF")
        self.vibration.off()

    def _on(self) -> None:
        print("[vibrator] ON")
        self.vibration.on()
