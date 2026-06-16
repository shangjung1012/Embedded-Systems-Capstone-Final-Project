from __future__ import annotations

import argparse
import json
from pathlib import Path

from preprocess.srt import parse_srt
from preprocess.timeline import build_timeline
from preprocess.video import build_video_color_events
from preprocess.gemini_video import (
    DEFAULT_GEMINI_CREDENTIALS,
    DEFAULT_GEMINI_MODEL,
    build_gemini_video_events,
)


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
    parser.add_argument(
        "--fan-duration-ms",
        type=int,
        default=2000,
        help="Maximum fan duration per matched cue. Use 0 to keep the full cue duration.",
    )
    parser.add_argument(
        "--vibration-duration-ms",
        type=int,
        default=2000,
        help="Maximum vibration duration per matched cue. Use 0 to keep the full cue duration.",
    )
    parser.add_argument(
        "--gemini-video",
        action="store_true",
        help="Enable Gemini frame analysis for mist, vibration, and fan events.",
    )
    parser.add_argument(
        "--gemini-credentials",
        type=Path,
        default=DEFAULT_GEMINI_CREDENTIALS,
        help=f"Service account JSON for Vertex AI Gemini. Defaults to {DEFAULT_GEMINI_CREDENTIALS}.",
    )
    parser.add_argument(
        "--gemini-project",
        help="Google Cloud project for Vertex AI. Defaults to project_id in the service account JSON.",
    )
    parser.add_argument(
        "--gemini-location",
        default="us-central1",
        help="Vertex AI location for Gemini. Defaults to us-central1.",
    )
    parser.add_argument(
        "--gemini-model",
        default=DEFAULT_GEMINI_MODEL,
        help=f"Gemini model name. Defaults to {DEFAULT_GEMINI_MODEL}.",
    )
    parser.add_argument(
        "--gemini-interval-ms",
        type=int,
        default=3000,
        help="Frame sampling interval for Gemini video analysis.",
    )
    parser.add_argument(
        "--gemini-event-duration-ms",
        type=int,
        default=0,
        help="Deprecated. Gemini events now follow sampled frame spans.",
    )
    parser.add_argument(
        "--gemini-hold-frames",
        type=int,
        default=1,
        help="Keep Gemini effects alive across this many missed frame detections.",
    )
    parser.add_argument(
        "--gemini-request-delay-ms",
        type=int,
        default=0,
        help="Delay between Gemini API requests to reduce rate-limit errors.",
    )
    parser.add_argument(
        "--gemini-min-confidence",
        type=float,
        default=0.55,
        help="Minimum Gemini confidence required to add an event.",
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
    gemini_video_events = []
    if args.gemini_video:
        gemini_video_events = build_gemini_video_events(
            args.video,
            credentials_path=args.gemini_credentials,
            project=args.gemini_project,
            location=args.gemini_location,
            model=args.gemini_model,
            interval_ms=args.gemini_interval_ms,
            min_confidence=args.gemini_min_confidence,
            hold_frames=args.gemini_hold_frames,
            request_delay_ms=args.gemini_request_delay_ms,
        )
    timeline = build_timeline(
        cues,
        subtitle_path,
        include_neutral=args.include_neutral,
        extra_events=[*video_color_events, *gemini_video_events],
        fan_duration_ms=_duration_limit(args.fan_duration_ms),
        vibration_duration_ms=_duration_limit(args.vibration_duration_ms),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    entry_count = sum(len(schedule) for schedule in timeline.values())
    print(f"Wrote {entry_count} module schedule entries to {output_path}")
    return 0


def _duration_limit(value: int) -> int | None:
    return value if value > 0 else None
