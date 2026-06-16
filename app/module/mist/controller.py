from __future__ import annotations

import time

from app.gpio import GpioPins, create_output_device


class MistController:
    def __init__(self) -> None:
        # active_high=False: .on() → GPIO LOW (霧化開), .off() → GPIO HIGH (霧化關)
        self.mist = create_output_device(GpioPins.MIST, active_high=False)
        self.mist.off()

    def apply(self, config: dict[str, object]) -> None:
        enabled = bool(config.get("enabled", False))
        print(f"[mist] enabled={str(enabled).lower()}")
        if enabled:
            self._on()
        else:
            self._off()

    def off(self) -> None:
        self.apply({"enabled": False})

    def _on(self) -> None:
        self.mist.on()  # GPIO LOW → 霧化開啟

    def _off(self) -> None:
        # 改了可能會關不掉
        self.mist.off()     # GPIO HIGH
        time.sleep(0.1)
        self.mist.on()      # GPIO LOW
        time.sleep(0.1)
        self.mist.off()     # GPIO HIGH → 關閉
