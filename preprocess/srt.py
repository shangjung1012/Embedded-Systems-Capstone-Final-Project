from __future__ import annotations

from dataclasses import dataclass
import re


TIMECODE_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)


@dataclass(frozen=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)


def parse_timecode(value: str) -> int:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    whole_seconds, milliseconds = seconds.split(".")
    return (
        int(hours) * 3_600_000
        + int(minutes) * 60_000
        + int(whole_seconds) * 1_000
        + int(milliseconds)
    )


def format_timecode(milliseconds: int) -> str:
    milliseconds = max(0, milliseconds)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def parse_srt(content: str) -> list[Cue]:
    cues: list[Cue] = []
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n").strip())

    for fallback_index, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        time_line_index = 0 if TIMECODE_RE.search(lines[0]) else 1
        if time_line_index >= len(lines):
            raise ValueError(f"Invalid SRT block near cue {fallback_index}: missing timecode")

        match = TIMECODE_RE.search(lines[time_line_index])
        if not match:
            raise ValueError(f"Invalid SRT block near cue {fallback_index}: {block!r}")

        try:
            index = int(lines[0]) if time_line_index == 1 else fallback_index
        except ValueError:
            index = fallback_index

        text = " ".join(lines[time_line_index + 1 :])
        text = re.sub(r"<[^>]+>", "", text).strip()
        start_ms = parse_timecode(match.group("start"))
        end_ms = parse_timecode(match.group("end"))
        if end_ms <= start_ms:
            raise ValueError(f"Cue {index} ends before it starts")

        cues.append(Cue(index=index, start_ms=start_ms, end_ms=end_ms, text=text))

    return cues

