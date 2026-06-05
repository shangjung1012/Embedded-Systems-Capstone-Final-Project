from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from app.effects import EffectController, merge_active_effects
from app.player import VideoPlayer


class TimelineRuntime:
    def __init__(
        self,
        timeline_path: Path,
        *,
        video_path: Path | None = None,
        player: str = "auto",
        speed: float = 1.0,
        dry_run: bool = False,
    ) -> None:
        if speed <= 0:
            raise ValueError("speed must be greater than 0")
        self.timeline_path = timeline_path
        self.video_path = video_path
        self.player_name = "none" if dry_run else player
        self.speed = speed
        self.effects = EffectController.create()

    def preview(self) -> None:
        for event in self._load_events():
            print(_format_event(event))

    def run(self) -> None:
        events = self._load_events()
        player = VideoPlayer(self.video_path, self.player_name)
        active_events: list[dict[str, Any]] = []
        change_points = _build_change_points(events)

        try:
            player.start()
            started_at = time.monotonic()
            self.effects.off()

            for event_time_ms, action, event in change_points:
                wait_seconds = event_time_ms / 1000 / self.speed - (time.monotonic() - started_at)
                if wait_seconds > 0:
                    time.sleep(wait_seconds)

                if action == "start":
                    active_events.append(event)
                    print(f"[timeline] start {_format_event(event)}")
                else:
                    active_events = [active_event for active_event in active_events if active_event is not event]
                    print(f"[timeline] end cue={event['cue_index']}")

                self.effects.apply(merge_active_effects(active_events))

            player.wait()
        finally:
            self.effects.off()
            player.stop()

    def _load_events(self) -> list[dict[str, Any]]:
        if not self.timeline_path.exists():
            raise FileNotFoundError(f"Timeline file not found: {self.timeline_path}")

        timeline = json.loads(self.timeline_path.read_text(encoding="utf-8"))
        return sorted(timeline.get("events", []), key=lambda event: event["start_ms"])


def _build_change_points(events: list[dict[str, Any]]) -> list[tuple[int, str, dict[str, Any]]]:
    points: list[tuple[int, str, dict[str, Any]]] = []
    for event in events:
        points.append((int(event["start_ms"]), "start", event))
        points.append((int(event["end_ms"]), "end", event))
    return sorted(points, key=lambda point: (point[0], 0 if point[1] == "end" else 1))


def _format_event(event: dict[str, Any]) -> str:
    effects = event["effects"]
    led = effects["led"]
    return (
        f"{event['start']} -> {event['end']} "
        f"tags={','.join(event['tags']) or 'neutral'} "
        f"fan={effects['fan']['speed']} "
        f"mist={str(effects['mist']['enabled']).lower()} "
        f"vibration={effects['vibration']['intensity']} "
        f"led=rgb({led['rgb'][0]},{led['rgb'][1]},{led['rgb'][2]})@{led['brightness']}"
    )
