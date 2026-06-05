from __future__ import annotations


class MistController:
    def apply(self, config: dict[str, object]) -> None:
        enabled = bool(config.get("enabled", False))
        print(f"[mist] enabled={str(enabled).lower()}")

    def off(self) -> None:
        self.apply({"enabled": False})

