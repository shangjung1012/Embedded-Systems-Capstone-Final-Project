from __future__ import annotations

from pathlib import Path
from typing import Any

from preprocess.rules import NEUTRAL_EFFECTS
from preprocess.srt import format_timecode


ZONE_LED_COUNTS = {
    "right": 14,
    "top": 22,
    "left": 17,
}
_EDGE_SAMPLE_SIZE = (40, 32)


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
    previous_signature: list[int] | None = None
    event_start_ms = 0
    event_zones: dict[str, list[dict[str, Any]]] | None = None

    for current_ms in range(0, max(duration_ms, interval_ms), interval_ms):
        capture.set(cv2.CAP_PROP_POS_MSEC, current_ms)
        ok, frame = capture.read()
        if not ok:
            break

        zones = _frame_led_zones(frame, cv2)
        signature = _zones_signature(zones)
        if previous_signature is None:
            previous_signature = signature
            event_zones = zones
            event_start_ms = current_ms
            continue

        if _color_distance(previous_signature, signature) < color_change_threshold:
            continue

        events.append(_build_led_event(len(events) + 1, event_start_ms, current_ms, event_zones))
        previous_signature = signature
        event_zones = zones
        event_start_ms = current_ms

    capture.release()

    if previous_signature is not None and event_zones is not None:
        event_end_ms = duration_ms if duration_ms > event_start_ms else event_start_ms + interval_ms
        events.append(_build_led_event(len(events) + 1, event_start_ms, event_end_ms, event_zones))

    return events


def _frame_led_zones(frame: Any, cv2: Any) -> dict[str, list[dict[str, Any]]]:
    resized = cv2.resize(frame, _EDGE_SAMPLE_SIZE, interpolation=cv2.INTER_AREA)
    height, width = resized.shape[:2]
    return {
        "right": _sample_vertical_edge(resized, column=width - 1, count=ZONE_LED_COUNTS["right"], reverse=True),
        "top": _sample_horizontal_edge(resized, row=0, count=ZONE_LED_COUNTS["top"], reverse=True),
        "left": _sample_vertical_edge(resized, column=0, count=ZONE_LED_COUNTS["left"], reverse=False),
    }


def _sample_vertical_edge(frame: Any, *, column: int, count: int, reverse: bool) -> list[dict[str, Any]]:
    height = frame.shape[0]
    positions = _sample_positions(height, count, reverse=reverse)
    return [_pixel_config(frame[position, column]) for position in positions]


def _sample_horizontal_edge(frame: Any, *, row: int, count: int, reverse: bool) -> list[dict[str, Any]]:
    width = frame.shape[1]
    positions = _sample_positions(width, count, reverse=reverse)
    return [_pixel_config(frame[row, position]) for position in positions]


def _sample_positions(length: int, count: int, *, reverse: bool) -> list[int]:
    if count <= 1:
        positions = [0]
    else:
        positions = [round(index * (length - 1) / (count - 1)) for index in range(count)]
    if reverse:
        positions.reverse()
    return positions


def _pixel_config(pixel: Any) -> dict[str, Any]:
    blue, green, red = (int(value) for value in pixel[:3])
    brightness = max(0.08, min(1.0, max(red, green, blue) / 255))
    return {"rgb": [red, green, blue], "brightness": round(brightness, 2)}


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
    zones: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    effects = {
        **NEUTRAL_EFFECTS,
        "led": {"zones": zones},
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


def _zones_signature(zones: dict[str, list[dict[str, Any]]]) -> list[int]:
    pixels = [pixel for zone in zones.values() for pixel in zone]
    if not pixels:
        return [0, 0, 0]
    return [
        round(sum(pixel["rgb"][channel] for pixel in pixels) / len(pixels))
        for channel in range(3)
    ]
