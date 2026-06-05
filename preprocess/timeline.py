from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from preprocess.rules import NEUTRAL_EFFECTS, build_effects, match_rules
from preprocess.srt import Cue, format_timecode


def build_timeline(
    cues: list[Cue],
    subtitle_path: Path,
    *,
    include_neutral: bool = False,
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

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {"type": "srt", "path": str(subtitle_path)},
        "defaults": NEUTRAL_EFFECTS,
        "event_count": len(events),
        "events": events,
    }

