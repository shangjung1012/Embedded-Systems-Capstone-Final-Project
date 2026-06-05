from __future__ import annotations


class VibratorController:
    def apply(self, config: dict[str, object]) -> None:
        intensity = int(config.get("intensity", 0))
        print(f"[vibrator] intensity={_clamp(intensity)}")

    def off(self) -> None:
        self.apply({"intensity": 0})


def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))

