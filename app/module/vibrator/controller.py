from __future__ import annotations

try:
    from gpiozero import OutputDevice
except ImportError:  # Allows development on machines without gpiozero.
    OutputDevice = None  # type: ignore[assignment]


VIBRATION_GPIO = 17  # GPIO17 = physical pin 11


class VibratorController:
    def __init__(self) -> None:
        self.vibration = OutputDevice(VIBRATION_GPIO) if OutputDevice is not None else None

    def apply(self, config: dict[str, object]) -> None:
        intensity = int(config.get("intensity", 0))
        intensity = _clamp(intensity)
        if intensity > 0:
            self._on(intensity)
        else:
            self.off()

    def off(self) -> None:
        print("[vibrator] OFF")
        if self.vibration is not None:
            self.vibration.off()

    def _on(self, intensity: int) -> None:
        print(f"[vibrator] ON intensity={intensity}")
        if self.vibration is not None:
            self.vibration.on()


def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))
