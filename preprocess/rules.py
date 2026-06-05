from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class Rule:
    tag: str
    keywords: tuple[str, ...]
    effects: dict[str, Any]
    led_priority: int


RULES: tuple[Rule, ...] = (
    Rule(
        tag="rain",
        keywords=("rain", "raining", "drizzle", "wet", "umbrella", "下雨", "雨景", "雨"),
        effects={
            "fan": {"speed": 35},
            "mist": {"enabled": True},
            "vibration": {"intensity": 0},
            "led": {"rgb": [115, 130, 140], "brightness": 0.45},
        },
        led_priority=50,
    ),
    Rule(
        tag="storm",
        keywords=("storm", "thunder", "lightning", "暴雨", "風暴", "雷", "閃電"),
        effects={
            "fan": {"speed": 70},
            "mist": {"enabled": True},
            "vibration": {"intensity": 35},
            "led": {"rgb": [75, 95, 130], "brightness": 0.55},
        },
        led_priority=80,
    ),
    Rule(
        tag="snow",
        keywords=("snow", "snowy", "blizzard", "ice", "frozen", "cold", "雪景", "下雪", "雪", "冰"),
        effects={
            "fan": {"speed": 85},
            "mist": {"enabled": False},
            "vibration": {"intensity": 0},
            "led": {"rgb": [130, 190, 255], "brightness": 0.65},
        },
        led_priority=70,
    ),
    Rule(
        tag="wind",
        keywords=("wind", "windy", "breeze", "gust", "強風", "微風", "風"),
        effects={
            "fan": {"speed": 55},
            "mist": {"enabled": False},
            "vibration": {"intensity": 0},
            "led": {"rgb": [180, 210, 230], "brightness": 0.35},
        },
        led_priority=30,
    ),
    Rule(
        tag="racing",
        keywords=("race", "racing", "engine", "speed", "speeds", "fast", "賽車", "引擎", "奔馳", "速度"),
        effects={
            "fan": {"speed": 90},
            "mist": {"enabled": False},
            "vibration": {"intensity": 45},
            "led": {"rgb": [255, 70, 35], "brightness": 0.7},
        },
        led_priority=40,
    ),
    Rule(
        tag="impact",
        keywords=("crash", "collision", "impact", "explosion", "explode", "bump", "撞擊", "碰撞", "爆炸", "衝擊"),
        effects={
            "fan": {"speed": 45},
            "mist": {"enabled": False},
            "vibration": {"intensity": 100},
            "led": {"rgb": [255, 35, 20], "brightness": 1.0},
        },
        led_priority=90,
    ),
    Rule(
        tag="sunny",
        keywords=("sun", "sunny", "sunlight", "bright", "陽光", "日光", "晴天"),
        effects={
            "fan": {"speed": 15},
            "mist": {"enabled": False},
            "vibration": {"intensity": 0},
            "led": {"rgb": [255, 190, 80], "brightness": 0.8},
        },
        led_priority=60,
    ),
    Rule(
        tag="fog",
        keywords=("fog", "mist", "smoke", "霧", "霧氣", "水霧"),
        effects={
            "fan": {"speed": 20},
            "mist": {"enabled": True},
            "vibration": {"intensity": 0},
            "led": {"rgb": [170, 185, 190], "brightness": 0.4},
        },
        led_priority=65,
    ),
)


NEUTRAL_EFFECTS: dict[str, Any] = {
    "fan": {"speed": 0},
    "mist": {"enabled": False},
    "vibration": {"intensity": 0},
    "led": {"rgb": [0, 0, 0], "brightness": 0.0},
}


def match_rules(text: str) -> list[Rule]:
    normalized = text.casefold()
    matches: list[Rule] = []
    for rule in RULES:
        if any(_has_keyword(normalized, keyword.casefold()) for keyword in rule.keywords):
            matches.append(rule)
    return matches


def build_effects(rules: list[Rule]) -> dict[str, Any]:
    effects = {
        "fan": {"speed": 0},
        "mist": {"enabled": False},
        "vibration": {"intensity": 0},
        "led": {"rgb": [0, 0, 0], "brightness": 0.0},
    }
    led_priority = -1

    for rule in rules:
        rule_effects = rule.effects
        effects["fan"]["speed"] = max(effects["fan"]["speed"], rule_effects["fan"]["speed"])
        effects["mist"]["enabled"] = effects["mist"]["enabled"] or rule_effects["mist"]["enabled"]
        effects["vibration"]["intensity"] = max(
            effects["vibration"]["intensity"], rule_effects["vibration"]["intensity"]
        )
        if rule.led_priority > led_priority:
            effects["led"] = dict(rule_effects["led"])
            led_priority = rule.led_priority

    return effects


def _has_keyword(text: str, keyword: str) -> bool:
    if keyword.isascii() and any(character.isalnum() for character in keyword):
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return keyword in text
