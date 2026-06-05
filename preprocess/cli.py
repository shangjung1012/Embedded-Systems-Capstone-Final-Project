from __future__ import annotations

import argparse
import json
from pathlib import Path

from preprocess.srt import parse_srt
from preprocess.timeline import build_timeline


DEFAULT_SUBTITLE = Path("preprocess/subtitles/demo.srt")


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
    args = parser.parse_args(argv)

    subtitle_path = args.subtitle
    output_path = args.output or Path("preprocess/output") / f"{subtitle_path.stem}.timeline.json"

    cues = parse_srt(subtitle_path.read_text(encoding="utf-8"))
    timeline = build_timeline(cues, subtitle_path, include_neutral=args.include_neutral)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {timeline['event_count']} events to {output_path}")
    return 0

