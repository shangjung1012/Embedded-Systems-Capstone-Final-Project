from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any


DEFAULT_TIMELINE = Path("preprocess/output/demo.timeline.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or preview a generated 4D effect timeline.")
    parser.add_argument(
        "timeline",
        nargs="?",
        type=Path,
        default=DEFAULT_TIMELINE,
        help=f"Timeline JSON path. Defaults to {DEFAULT_TIMELINE}.",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Wait for each event start time. Without this flag, print a dry-run schedule.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Realtime playback speed multiplier. Example: 2.0 runs twice as fast.",
    )
    args = parser.parse_args()

    if args.speed <= 0:
        raise ValueError("--speed must be greater than 0")
    if not args.timeline.exists():
        print(f"Timeline file not found: {args.timeline}")
        print("Generate one first with: python -m preprocess")
        return 1

    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    events = timeline.get("events", [])

    if args.realtime:
        _run_realtime(events, args.speed)
    else:
        _print_schedule(events)
    return 0


def _print_schedule(events: list[dict[str, Any]]) -> None:
    for event in events:
        print(_format_event(event))


def _run_realtime(events: list[dict[str, Any]], speed: float) -> None:
    started_at = time.monotonic()
    for event in events:
        wait_seconds = event["start_ms"] / 1000 / speed - (time.monotonic() - started_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        print(f"START {_format_event(event)}")


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


if __name__ == "__main__":
    raise SystemExit(main())
