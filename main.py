from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from app.gpio import configure_gpio_pins
from app.runtime import TimelineRuntime


DEFAULT_TIMELINE = Path("preprocess/output/demo.timeline.json")
DEFAULT_VIDEO = Path("preprocess/video/demo.mp4")
TIMELINE_DIR = Path("preprocess/output")
VIDEO_DIR = Path("preprocess/video")


def main() -> int:
    parser = argparse.ArgumentParser(description="Play a video with a synchronized 4D effect timeline.")
    parser.add_argument(
        "timeline",
        nargs="?",
        type=Path,
        default=DEFAULT_TIMELINE,
        help=(
            "Timeline JSON path or media name. Example: 'demo2' resolves to "
            "preprocess/output/demo2.timeline.json and preprocess/video/demo2.mp4. "
            f"Defaults to {DEFAULT_TIMELINE}."
        ),
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=DEFAULT_VIDEO,
        help=f"Video path to play with the timeline. Defaults to {DEFAULT_VIDEO}.",
    )
    parser.add_argument(
        "--player",
        choices=("auto", "python", "ffplay", "cvlc", "vlc", "none"),
        default="auto",
        help="Video player backend. Use 'none' to run effects without opening video.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the timeline schedule without waiting or playing video.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the timeline clock and effect logs without opening the video player.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier for the timeline clock. Example: 2.0 runs twice as fast.",
    )
    parser.add_argument(
        "--status-window",
        action="store_true",
        help="Open a small realtime window showing current module states.",
    )
    parser.add_argument(
        "--modules",
        action="append",
        choices=None,
        help=(
            "Only run selected hardware modules while video plays. "
            "Use comma-separated names or repeat the option. Choices: fan,mist,vibration,led."
        ),
    )
    parser.add_argument(
        "--vibration-pin",
        type=int,
        help="BCM GPIO pin for the vibration module. Defaults to VIBRATION_PIN or 17.",
    )
    parser.add_argument(
        "--fan-ina-pin",
        type=int,
        help="BCM GPIO pin for the fan INA input. Defaults to FAN_INA_PIN or 22.",
    )
    parser.add_argument(
        "--fan-inb-pin",
        type=int,
        help="BCM GPIO pin for the fan INB input. Defaults to FAN_INB_PIN or 27.",
    )
    parser.add_argument(
        "--mist-pin",
        type=int,
        help="BCM GPIO pin for the mist module. Defaults to MIST_PIN or 23.",
    )
    args = parser.parse_args()
    enabled_modules = _parse_modules(args.modules)
    timeline_path, video_path = _resolve_media_paths(args.timeline, args.video)

    if not args.preview and os.geteuid() != 0:
        print(
            "main.py must be run as root for GPIO/LED hardware. "
            "Use: sudo uv run python main.py preprocess/output/demo.timeline.json",
            file=sys.stderr,
        )
        return 1

    configure_gpio_pins(
        vibration_pin=args.vibration_pin,
        fan_ina_pin=args.fan_ina_pin,
        fan_inb_pin=args.fan_inb_pin,
        mist_pin=args.mist_pin,
    )

    runtime = TimelineRuntime(
        timeline_path,
        video_path=video_path,
        player=args.player,
        speed=args.speed,
        dry_run=args.dry_run,
        status_window=args.status_window,
        enabled_modules=enabled_modules,
    )
    if args.preview:
        runtime.preview()
    else:
        runtime.run()
    return 0


def _resolve_media_paths(timeline: Path, video: Path) -> tuple[Path, Path]:
    if _is_short_media_name(timeline):
        name = timeline.name
        return TIMELINE_DIR / f"{name}.timeline.json", VIDEO_DIR / f"{name}.mp4"
    return timeline, video


def _is_short_media_name(value: Path) -> bool:
    return len(value.parts) == 1 and value.suffix == ""

def _parse_modules(values: list[str] | None) -> set[str] | None:
    if not values:
        return None

    modules = {
        module.strip().lower()
        for value in values
        for module in value.split(",")
        if module.strip()
    }
    valid_modules = {"fan", "mist", "vibration", "led"}
    invalid_modules = sorted(modules - valid_modules)
    if invalid_modules:
        raise SystemExit(f"Unknown module(s): {', '.join(invalid_modules)}")
    return modules


if __name__ == "__main__":
    raise SystemExit(main())
