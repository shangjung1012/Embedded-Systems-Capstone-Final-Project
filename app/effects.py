from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from app.module.fan import FanController
from app.module.light import LightController
from app.module.mist import MistController
from app.module.vibrator import VibratorController


DEFAULT_EFFECTS: dict[str, Any] = {
    "fan": {"speed": 0},
    "mist": {"enabled": False},
    "vibration": {"intensity": 0},
    "led": {"rgb": [0, 0, 0], "brightness": 0.0},
}


@dataclass
class EffectController:
    fan: FanController
    light: LightController
    mist: MistController
    vibrator: VibratorController
    last_effects: dict[str, Any] | None = None

    @classmethod
    def create(cls) -> "EffectController":
        return cls(
            fan=FanController(),
            light=LightController(),
            mist=MistController(),
            vibrator=VibratorController(),
        )

    def apply(self, effects: dict[str, Any]) -> None:
        normalized = {
            "fan": effects.get("fan", DEFAULT_EFFECTS["fan"]),
            "mist": effects.get("mist", DEFAULT_EFFECTS["mist"]),
            "vibration": effects.get("vibration", DEFAULT_EFFECTS["vibration"]),
            "led": effects.get("led", DEFAULT_EFFECTS["led"]),
        }
        if normalized == self.last_effects:
            return

        previous = self.last_effects or {}
        if normalized["fan"] != previous.get("fan"):
            self.fan.apply(normalized["fan"])
        if normalized["mist"] != previous.get("mist"):
            self.mist.apply(normalized["mist"])
        if normalized["vibration"] != previous.get("vibration"):
            self.vibrator.apply(normalized["vibration"])
        if normalized["led"] != previous.get("led"):
            self.light.apply(normalized["led"])
        self.last_effects = deepcopy(normalized)

    def off(self) -> None:
        self.apply(DEFAULT_EFFECTS)


def merge_active_effects(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return DEFAULT_EFFECTS

    merged = {
        "fan": {"speed": 0},
        "mist": {"enabled": False},
        "vibration": {"intensity": 0},
        "led": {"rgb": [0, 0, 0], "brightness": 0.0},
    }
    video_led_events = [
        event for event in events if event.get("source") == "video" and "led" in event.get("effects", {})
    ]
    led_events = video_led_events or [event for event in events if "led" in event.get("effects", {})]
    newest_led_event = max(led_events, key=lambda event: event["start_ms"]) if led_events else None

    for event in events:
        effects = event["effects"]
        fan = effects.get("fan", DEFAULT_EFFECTS["fan"])
        mist = effects.get("mist", DEFAULT_EFFECTS["mist"])
        vibration = effects.get("vibration", DEFAULT_EFFECTS["vibration"])
        merged["fan"]["speed"] = max(merged["fan"]["speed"], int(fan["speed"]))
        merged["mist"]["enabled"] = merged["mist"]["enabled"] or bool(mist["enabled"])
        merged["vibration"]["intensity"] = max(
            merged["vibration"]["intensity"], int(vibration["intensity"])
        )

    if newest_led_event is not None:
        merged["led"] = dict(newest_led_event["effects"].get("led", DEFAULT_EFFECTS["led"]))
    return merged
