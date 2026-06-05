from __future__ import annotations


class LightController:
    def apply(self, config: dict[str, object]) -> None:
        rgb = config.get("rgb", [0, 0, 0])
        brightness = float(config.get("brightness", 0.0))
        if not isinstance(rgb, list) or len(rgb) != 3:
            rgb = [0, 0, 0]
        red, green, blue = (_clamp(int(value), 0, 255) for value in rgb)
        brightness = max(0.0, min(1.0, brightness))
        print(f"[light] rgb=({red},{green},{blue}) brightness={brightness:.2f}")

    def off(self) -> None:
        self.apply({"rgb": [0, 0, 0], "brightness": 0.0})


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))

