from __future__ import annotations

import argparse
from pathlib import Path

from app.runtime import TimelineRuntime


DEFAULT_TIMELINE = Path("preprocess/output/demo.timeline.json")
DEFAULT_VIDEO = Path("preprocess/video/demo.mp4")


def main() -> int:
    parser = argparse.ArgumentParser(description="Play a video with a synchronized 4D effect timeline.")
    parser.add_argument(
        "timeline",
        nargs="?",
        type=Path,
        default=DEFAULT_TIMELINE,
        help=f"Timeline JSON path. Defaults to {DEFAULT_TIMELINE}.",
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
    args = parser.parse_args()

    runtime = TimelineRuntime(
        args.timeline,
        video_path=args.video,
        player=args.player,
        speed=args.speed,
        dry_run=args.dry_run,
        status_window=args.status_window,
    )
    if args.preview:
        runtime.preview()
    else:
        runtime.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
