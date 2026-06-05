from __future__ import annotations

import argparse
import json
from pathlib import Path

from preprocess.srt import parse_srt
from preprocess.timeline import build_timeline
from preprocess.video import build_video_color_events


DEFAULT_SUBTITLE = Path("preprocess/subtitles/demo.srt")
DEFAULT_VIDEO = Path("preprocess/video/demo.mp4")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a hardware effect timeline JSON file from an SRT subtitle file."
    )
    parser.add_argument(
        "subtitle",
        nargs="?",
        type=Path,
        default=DEFAULT_SUBTITLE,
        help=f"SRT subtitle path. Defaults to {DEFAULT_SUBTITLE}.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Timeline JSON output path. Defaults to preprocess/output/<subtitle-name>.timeline.json.",
    )
    parser.add_argument(
        "--include-neutral",
        action="store_true",
        help="Include subtitle cues with no matched effect keywords as neutral events.",
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=DEFAULT_VIDEO,
        help=f"Video path for OpenCV LED color analysis. Defaults to {DEFAULT_VIDEO}.",
    )
    parser.add_argument(
        "--no-video-color",
        action="store_true",
        help="Disable OpenCV frame color analysis for LED timeline events.",
    )
    parser.add_argument(
        "--color-interval-ms",
        type=int,
        default=500,
        help="Frame sampling interval for LED color analysis.",
    )
    parser.add_argument(
        "--color-threshold",
        type=int,
        default=10,
        help="Minimum RGB channel change required to start a new LED color event.",
    )
    args = parser.parse_args(argv)

    subtitle_path = args.subtitle
    output_path = args.output or Path("preprocess/output") / f"{subtitle_path.stem}.timeline.json"

    cues = parse_srt(subtitle_path.read_text(encoding="utf-8"))
    video_color_events = []
    if not args.no_video_color:
        video_color_events = build_video_color_events(
            args.video,
            interval_ms=args.color_interval_ms,
            color_change_threshold=args.color_threshold,
        )
    timeline = build_timeline(
        cues,
        subtitle_path,
        include_neutral=args.include_neutral,
        extra_events=video_color_events,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    entry_count = sum(len(schedule) for schedule in timeline.values())
    print(f"Wrote {entry_count} module schedule entries to {output_path}")
    return 0
