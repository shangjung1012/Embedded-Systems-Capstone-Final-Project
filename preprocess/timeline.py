from __future__ import annotations

from pathlib import Path
from typing import Any

from preprocess.rules import NEUTRAL_EFFECTS, build_effects, match_rules
from preprocess.srt import Cue, format_timecode


MODULE_KEYS = ("fan", "mist", "vibration", "led")


def build_timeline(
    cues: list[Cue],
    subtitle_path: Path,
    *,
    include_neutral: bool = False,
    extra_events: list[dict[str, Any]] | None = None,
    fan_duration_ms: int | None = 2_000,
    vibration_duration_ms: int | None = 2_000,
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []

    for cue in cues:
        matched_rules = match_rules(cue.text)
        if not matched_rules and not include_neutral:
            continue

        tags = [rule.tag for rule in matched_rules]
        effects = build_effects(matched_rules) if matched_rules else NEUTRAL_EFFECTS
        events.append(
            {
                "id": f"subtitle-{cue.index}",
                "source": "subtitle",
                "cue_index": cue.index,
                "start_ms": cue.start_ms,
                "end_ms": cue.end_ms,
                "start": format_timecode(cue.start_ms),
                "end": format_timecode(cue.end_ms),
                "duration_ms": cue.duration_ms,
                "text": cue.text,
                "tags": tags,
                "effects": effects,
            }
        )

    if extra_events:
        events.extend(extra_events)

    events.sort(key=lambda event: (event["start_ms"], event["end_ms"], event.get("id", "")))

    module_duration_limits = {
        "fan": fan_duration_ms,
        "vibration": vibration_duration_ms,
    }
    modules = _build_module_schedules(events, module_duration_limits=module_duration_limits)

    return modules


def _build_module_schedules(
    events: list[dict[str, Any]],
    *,
    module_duration_limits: dict[str, int | None] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    modules: dict[str, list[dict[str, Any]]] = {module: [] for module in MODULE_KEYS}
    module_duration_limits = module_duration_limits or {}

    for event in events:
        effects = event["effects"]
        for module in MODULE_KEYS:
            config = effects.get(module)
            if config is None or config == NEUTRAL_EFFECTS[module]:
                continue

            start_ms = int(event["start_ms"])
            event_duration_limits = event.get("duration_limits", {})
            if isinstance(event_duration_limits, dict) and module in event_duration_limits:
                duration_limit_ms = event_duration_limits[module]
            else:
                duration_limit_ms = module_duration_limits.get(module)
            end_ms = _limited_end_ms(
                start_ms,
                int(event["end_ms"]),
                duration_limit_ms,
            )
            modules[module].append({
                "start": format_timecode(start_ms),
                "end": format_timecode(end_ms),
                **config,
            })

    for schedule in modules.values():
        schedule.sort(key=lambda item: (item["start"], item["end"]))

    return modules


def _limited_end_ms(start_ms: int, end_ms: int, duration_limit_ms: int | None) -> int:
    if duration_limit_ms is None or duration_limit_ms <= 0:
        return end_ms
    return min(end_ms, start_ms + duration_limit_ms)
