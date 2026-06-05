from __future__ import annotations


class FanController:
    def apply(self, config: dict[str, object]) -> None:
        speed = int(config.get("speed", 0))
        print(f"[fan] speed={_clamp(speed)}")

    def off(self) -> None:
        self.apply({"speed": 0})


def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))

