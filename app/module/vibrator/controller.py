from __future__ import annotations

from app.gpio import GpioPins, create_output_device


class VibratorController:
    def __init__(self) -> None:
        self.vibration = create_output_device(GpioPins.VIBRATION)

    def apply(self, config: dict[str, object]) -> None:
        intensity = int(config.get("intensity", 0))
        intensity = _clamp(intensity)
        if intensity > 0:
            self._on(intensity)
        else:
            self.off()

    def off(self) -> None:
        print("[vibrator] OFF")
        self.vibration.off()

    def _on(self, intensity: int) -> None:
        print(f"[vibrator] ON intensity={intensity}")
        self.vibration.on()


def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))
