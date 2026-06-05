from __future__ import annotations

from pathlib import Path
from typing import Any

from preprocess.rules import NEUTRAL_EFFECTS
from preprocess.srt import format_timecode


def build_video_color_events(
    video_path: Path,
    *,
    interval_ms: int = 500,
    color_change_threshold: int = 10,
) -> list[dict[str, Any]]:
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("OpenCV is required for video color analysis. Install opencv-python-headless.") from error

    if interval_ms <= 0:
        raise ValueError("interval_ms must be greater than 0")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_ms = int(frame_count / fps * 1000) if frame_count > 0 else 0
    events: list[dict[str, Any]] = []
    previous_rgb: list[int] | None = None
    event_start_ms = 0
    event_rgb = [0, 0, 0]
    event_brightness = 0.0

    for current_ms in range(0, max(duration_ms, interval_ms), interval_ms):
        capture.set(cv2.CAP_PROP_POS_MSEC, current_ms)
        ok, frame = capture.read()
        if not ok:
            break

        rgb, brightness = _frame_led_color(frame, cv2)
        if previous_rgb is None:
            previous_rgb = rgb
            event_rgb = rgb
            event_brightness = brightness
            event_start_ms = current_ms
            continue

        if _color_distance(previous_rgb, rgb) < color_change_threshold:
            continue

        events.append(_build_led_event(len(events) + 1, event_start_ms, current_ms, event_rgb, event_brightness))
        previous_rgb = rgb
        event_rgb = rgb
        event_brightness = brightness
        event_start_ms = current_ms

    capture.release()

    if previous_rgb is not None:
        event_end_ms = duration_ms if duration_ms > event_start_ms else event_start_ms + interval_ms
        events.append(_build_led_event(len(events) + 1, event_start_ms, event_end_ms, event_rgb, event_brightness))

    return events


def _frame_led_color(frame: Any, cv2: Any) -> tuple[list[int], float]:
    resized = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    value = hsv[:, :, 2]
    mask = value > 24
    pixels = resized[mask] if mask.any() else resized.reshape(-1, 3)

    mean_bgr = pixels.mean(axis=0)
    blue, green, red = (int(round(channel)) for channel in mean_bgr)
    brightness = max(0.08, min(1.0, float(value.mean()) / 255))
    return [red, green, blue], round(brightness, 2)


def _build_led_event(
    index: int,
    start_ms: int,
    end_ms: int,
    rgb: list[int],
    brightness: float,
) -> dict[str, Any]:
    effects = {
        **NEUTRAL_EFFECTS,
        "led": {"rgb": rgb, "brightness": brightness},
    }
    return {
        "id": f"video-color-{index:04d}",
        "source": "video",
        "start_ms": start_ms,
        "end_ms": end_ms,
        "start": format_timecode(start_ms),
        "end": format_timecode(end_ms),
        "duration_ms": max(0, end_ms - start_ms),
        "text": "",
        "tags": ["video_color"],
        "effects": effects,
    }


def _color_distance(left: list[int], right: list[int]) -> int:
    return max(abs(left[index] - right[index]) for index in range(3))

