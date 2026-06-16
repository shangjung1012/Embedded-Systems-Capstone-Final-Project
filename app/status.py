from __future__ import annotations

import sys
from typing import Any, Protocol

from app.effects import DEFAULT_EFFECTS


class StatusMonitor(Protocol):
    def update(self, elapsed_ms: int, effects: dict[str, Any]) -> None:
        pass

    def close(self) -> None:
        pass


class NullStatusMonitor:
    def update(self, elapsed_ms: int, effects: dict[str, Any]) -> None:
        pass

    def close(self) -> None:
        pass


class TkStatusWindow:
    def __init__(self) -> None:
        import tkinter as tk

        self.tk = tk
        self.closed = False
        self.root = tk.Tk()
        self.root.title("4D Runtime Status")
        self.root.geometry("420x190")
        self.root.resizable(False, False)

        self.time_var = tk.StringVar(value="time: 00:00:00.000")
        self.fan_var = tk.StringVar(value="fan: off")
        self.mist_var = tk.StringVar(value="mist: off")
        self.vibration_var = tk.StringVar(value="vibration: off")
        self.led_var = tk.StringVar(value="led: rgb(0,0,0) @ 0.00")

        root = self.root
        tk.Label(root, textvariable=self.time_var, anchor="w", font=("Arial", 14, "bold")).pack(
            fill="x", padx=16, pady=(14, 8)
        )
        tk.Label(root, textvariable=self.fan_var, anchor="w", font=("Arial", 13)).pack(fill="x", padx=16)
        tk.Label(root, textvariable=self.mist_var, anchor="w", font=("Arial", 13)).pack(fill="x", padx=16)
        tk.Label(root, textvariable=self.vibration_var, anchor="w", font=("Arial", 13)).pack(fill="x", padx=16)

        led_frame = tk.Frame(root)
        led_frame.pack(fill="x", padx=16, pady=(6, 0))
        self.led_swatch = tk.Label(led_frame, width=4, height=2, bg="#000000", relief="solid")
        self.led_swatch.pack(side="left")
        tk.Label(led_frame, textvariable=self.led_var, anchor="w", font=("Arial", 13)).pack(
            side="left", fill="x", padx=10
        )

        self.root.update()

    def update(self, elapsed_ms: int, effects: dict[str, Any]) -> None:
        if self.closed:
            return

        normalized = normalize_effects(effects)
        fan = normalized["fan"]
        mist = normalized["mist"]
        vibration = normalized["vibration"]
        led = normalized["led"]
        red, green, blue = led["rgb"]

        self.time_var.set(f"time: {format_timecode(elapsed_ms)}")
        self.fan_var.set(f"fan: {'on' if fan['enabled'] else 'off'}")
        self.mist_var.set(f"mist: {'on' if mist['enabled'] else 'off'}")
        self.vibration_var.set(f"vibration: {'on' if vibration['enabled'] else 'off'}")
        self.led_var.set(f"led: rgb({red},{green},{blue}) @ {led['brightness']:.2f}")
        self.led_swatch.configure(bg=f"#{red:02x}{green:02x}{blue:02x}")
        try:
            self.root.update_idletasks()
            self.root.update()
        except self.tk.TclError:
            self.closed = True

    def close(self) -> None:
        if self.closed:
            return

        try:
            self.root.destroy()
            self.closed = True
        except self.tk.TclError:
            self.closed = True


def build_status_monitor(*, window: bool) -> StatusMonitor:
    if not window:
        return NullStatusMonitor()
    try:
        return TkStatusWindow()
    except Exception as error:
        print(f"[status] could not open status window: {error}", file=sys.stderr)
        return NullStatusMonitor()


def normalize_effects(effects: dict[str, Any]) -> dict[str, Any]:
    led = effects.get("led", DEFAULT_EFFECTS["led"])
    return {
        "fan": {"enabled": bool(effects.get("fan", DEFAULT_EFFECTS["fan"])["enabled"])},
        "mist": {"enabled": bool(effects.get("mist", DEFAULT_EFFECTS["mist"])["enabled"])},
        "vibration": {"enabled": bool(effects.get("vibration", DEFAULT_EFFECTS["vibration"])["enabled"])},
        "led": {
            "rgb": [int(value) for value in led["rgb"]],
            "brightness": float(led["brightness"]),
        },
    }


def format_timecode(milliseconds: int) -> str:
    milliseconds = max(0, milliseconds)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
