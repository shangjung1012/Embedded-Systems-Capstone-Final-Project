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

    modules = _build_module_schedules(events)

    return modules


def _build_module_schedules(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    modules: dict[str, list[dict[str, Any]]] = {module: [] for module in MODULE_KEYS}

    for event in events:
        effects = event["effects"]
        for module in MODULE_KEYS:
            config = effects.get(module)
            if config is None or config == NEUTRAL_EFFECTS[module]:
                continue

            modules[module].append({
                "start": event["start"],
                "end": event["end"],
                **config,
            })

    for schedule in modules.values():
        schedule.sort(key=lambda item: (item["start"], item["end"]))

    return modules
