from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from app.effects import DEFAULT_EFFECTS, EffectController, merge_active_effects
from app.player import VideoPlayer
from app.status import StatusMonitor, build_status_monitor


class TimelineRuntime:
    def __init__(
        self,
        timeline_path: Path,
        *,
        video_path: Path | None = None,
        player: str = "auto",
        speed: float = 1.0,
        dry_run: bool = False,
        status_window: bool = False,
    ) -> None:
        if speed <= 0:
            raise ValueError("speed must be greater than 0")
        self.timeline_path = timeline_path
        self.video_path = video_path
        self.player_name = "none" if dry_run else player
        self.speed = speed
        self.effects = EffectController.create()
        self.status_monitor = build_status_monitor(window=status_window)

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
            current_elapsed_ms = 0
            current_effects = DEFAULT_EFFECTS
            self.effects.off()
            self.status_monitor.update(0, current_effects)

            for event_time_ms, action, event in change_points:
                current_elapsed_ms = event_time_ms
                _wait_until(event_time_ms, started_at, self.speed, self.status_monitor, current_effects)

                if action == "start":
                    active_events.append(event)
                    print(f"[timeline] start {_format_event(event)}")
                else:
                    active_events = [active_event for active_event in active_events if active_event is not event]
                    print(f"[timeline] end {_event_label(event)}")

                current_effects = merge_active_effects(active_events)
                self.effects.apply(current_effects)
                self.status_monitor.update(event_time_ms, current_effects)

            _wait_for_player(player, started_at, self.speed, self.status_monitor, current_effects)
        finally:
            self.effects.off()
            shutdown_elapsed_ms = (
                _timeline_elapsed_ms(locals()["started_at"], self.speed)
                if "started_at" in locals()
                else locals().get("current_elapsed_ms", 0)
            )
            self.status_monitor.update(shutdown_elapsed_ms, DEFAULT_EFFECTS)
            self.status_monitor.close()
            player.stop()

    def _load_events(self) -> list[dict[str, Any]]:
        if not self.timeline_path.exists():
            raise FileNotFoundError(f"Timeline file not found: {self.timeline_path}")

        timeline = json.loads(self.timeline_path.read_text(encoding="utf-8"))
        if _is_module_schedule(timeline):
            events = _events_from_module_schedules(timeline)
        elif "modules" in timeline:
            events = _events_from_module_schedules(timeline["modules"])
        else:
            events = timeline.get("events", [])
        return sorted(events, key=lambda event: (event["start_ms"], event["end_ms"], event.get("id", "")))


def _build_change_points(events: list[dict[str, Any]]) -> list[tuple[int, str, dict[str, Any]]]:
    points: list[tuple[int, str, dict[str, Any]]] = []
    for event in events:
        points.append((int(event["start_ms"]), "start", event))
        points.append((int(event["end_ms"]), "end", event))
    return sorted(points, key=lambda point: (point[0], 0 if point[1] == "start" else 1))


def _wait_until(
    target_ms: int,
    started_at: float,
    speed: float,
    status_monitor: StatusMonitor,
    current_effects: dict[str, Any],
) -> None:
    while True:
        elapsed_ms = _timeline_elapsed_ms(started_at, speed)
        if elapsed_ms >= target_ms:
            return

        status_monitor.update(elapsed_ms, current_effects)
        remaining_seconds = (target_ms - elapsed_ms) / 1000 / speed
        time.sleep(min(0.05, max(0.005, remaining_seconds)))


def _wait_for_player(
    player: VideoPlayer,
    started_at: float,
    speed: float,
    status_monitor: StatusMonitor,
    current_effects: dict[str, Any],
) -> None:
    if player.process is None:
        return

    while player.is_running():
        status_monitor.update(_timeline_elapsed_ms(started_at, speed), current_effects)
        time.sleep(0.05)


def _timeline_elapsed_ms(started_at: float, speed: float) -> int:
    return int((time.monotonic() - started_at) * 1000 * speed)


def _events_from_module_schedules(modules: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    module_to_effect_key = {
        "fan": "fan",
        "mist": "mist",
        "vibration": "vibration",
        "led": "led",
    }

    for module, schedule in modules.items():
        effect_key = module_to_effect_key.get(module)
        if effect_key is None:
            continue

        for item in schedule:
            start_ms = item.get("start_ms", _parse_timecode(item["start"]))
            end_ms = item.get("end_ms", _parse_timecode(item["end"]))
            config = item.get("config") or _config_from_schedule_item(module, item)
            events.append(
                {
                    "id": item.get("id", f"{module}-{start_ms}-{end_ms}"),
                    "source": item.get("source", module),
                    "module": module,
                    "cue_index": item.get("cue_index"),
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "start": item["start"],
                    "end": item["end"],
                    "duration_ms": item.get("duration_ms", max(0, end_ms - start_ms)),
                    "tags": item.get("tags", []),
                    "effects": {effect_key: config},
                }
            )

    return events


def _is_module_schedule(timeline: dict[str, Any]) -> bool:
    return all(module in timeline and isinstance(timeline[module], list) for module in ("fan", "mist", "vibration", "led"))


def _parse_timecode(value: str) -> int:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    whole_seconds, milliseconds = seconds.split(".")
    return (
        int(hours) * 3_600_000
        + int(minutes) * 60_000
        + int(whole_seconds) * 1_000
        + int(milliseconds)
    )


def _config_from_schedule_item(module: str, item: dict[str, Any]) -> dict[str, Any]:
    if module == "fan":
        return {"enabled": item["enabled"]}
    if module == "mist":
        return {"enabled": item["enabled"]}
    if module == "vibration":
        return {"enabled": item["enabled"]}
    if module == "led":
        return {"rgb": item["rgb"], "brightness": item["brightness"]}
    return {}


def _format_event(event: dict[str, Any]) -> str:
    if event.get("module"):
        module = event["module"]
        effect_key = "led" if module == "led" else module
        config = event["effects"].get(effect_key, {})
        return (
            f"{event['start']} -> {event['end']} "
            f"module={module} "
            f"config={config}"
        )

    effects = event["effects"]
    fan = effects.get("fan", {"enabled": False})
    mist = effects.get("mist", {"enabled": False})
    vibration = effects.get("vibration", {"enabled": False})
    led = effects.get("led", {"rgb": [0, 0, 0], "brightness": 0.0})
    return (
        f"{event['start']} -> {event['end']} "
        f"tags={','.join(event['tags']) or 'neutral'} "
        f"fan={str(fan['enabled']).lower()} "
        f"mist={str(mist['enabled']).lower()} "
        f"vibration={str(vibration['enabled']).lower()} "
        f"led=rgb({led['rgb'][0]},{led['rgb'][1]},{led['rgb'][2]})@{led['brightness']}"
    )


def _event_label(event: dict[str, Any]) -> str:
    if event.get("module"):
        return f"module={event['module']} id={event.get('id', 'unknown')}"
    if event.get("cue_index") is not None:
        return f"cue={event['cue_index']}"
    return f"id={event.get('id', 'unknown')}"
