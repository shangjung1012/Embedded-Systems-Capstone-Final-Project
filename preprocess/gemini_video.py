from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from preprocess.rules import NEUTRAL_EFFECTS
from preprocess.srt import format_timecode


DEFAULT_GEMINI_CREDENTIALS = Path("preprocess/service_account.json")
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You classify one sampled video frame for a Raspberry Pi 4D video prototype.

Choose exactly one tag:
- spray: anything visibly spraying, bursting, splashing, steaming, smoking, raining,
  or ejecting outward where mist/humid spray should run.
- speed: walking, running, jumping, driving, riding, flying, chasing, fast travel,
  acceleration, fast camera motion, or anything with motion or a sense of speed
  where airflow should run.
- shake: a crash, collision, hit, explosion, strong shaking, screen shake, or
  anything that should create a vibration feeling. Do not choose shake for normal
  walking, jumping, running, or driving unless there is an impact or violent shake.
- none: no hardware effect is appropriate.

Hardware mapping:
- spray -> mist
- speed -> fan
- shake -> vibration
- none -> no effect

Return only JSON with this shape:
{"tag":"spray|shake|speed|none","confidence":0.0,"reason":"short phrase"}
""".strip()


@dataclass(frozen=True)
class GeminiFrameResult:
    tag: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class GeminiFrameSample:
    timestamp_ms: int
    result: GeminiFrameResult


def build_gemini_video_events(
    video_path: Path,
    *,
    credentials_path: Path | None = DEFAULT_GEMINI_CREDENTIALS,
    project: str | None = None,
    location: str = "us-central1",
    model: str = DEFAULT_GEMINI_MODEL,
    interval_ms: int = 3_000,
    min_confidence: float = 0.55,
    hold_frames: int = 1,
    request_delay_ms: int = 0,
) -> list[dict[str, Any]]:
    if interval_ms <= 0:
        raise ValueError("interval_ms must be greater than 0")
    if hold_frames < 0:
        raise ValueError("hold_frames must be greater than or equal to 0")
    if request_delay_ms < 0:
        raise ValueError("request_delay_ms must be greater than or equal to 0")

    try:
        import cv2
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise RuntimeError(
            "Gemini video analysis requires google-genai and opencv-python-headless. "
            "Install dependencies with uv sync."
        ) from error

    credentials_path = _configure_credentials(credentials_path)
    project = project or _project_from_service_account(credentials_path)
    if not project:
        raise ValueError(
            "Gemini Vertex AI requires a Google Cloud project. Pass --gemini-project "
            "or use a service account JSON that contains project_id."
        )

    client = genai.Client(vertexai=True, project=project, location=location)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_ms = int(frame_count / fps * 1000) if frame_count > 0 else 0
    continuous_samples: list[GeminiFrameSample] = []

    for current_ms in range(0, max(duration_ms, interval_ms), interval_ms):
        capture.set(cv2.CAP_PROP_POS_MSEC, current_ms)
        ok, frame = capture.read()
        if not ok:
            break

        jpeg_bytes = _encode_jpeg(frame, cv2)
        result = _classify_frame(
            client,
            types,
            model=model,
            jpeg_bytes=jpeg_bytes,
            timestamp_ms=current_ms,
        )
        if result.confidence < min_confidence:
            result = GeminiFrameResult(tag="none", confidence=result.confidence, reason=result.reason)

        continuous_samples.append(GeminiFrameSample(timestamp_ms=current_ms, result=result))
        if request_delay_ms > 0:
            time.sleep(request_delay_ms / 1000)

    capture.release()
    events = _build_continuous_events(
        continuous_samples,
        first_index=1,
        duration_ms=duration_ms,
        interval_ms=interval_ms,
        hold_frames=hold_frames,
    )
    events.sort(key=lambda event: (event["start_ms"], event["end_ms"], event["id"]))
    return events


def _configure_credentials(credentials_path: Path | None) -> Path | None:
    if credentials_path is None:
        return None

    if credentials_path.exists():
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(credentials_path))
        return credentials_path

    if credentials_path == DEFAULT_GEMINI_CREDENTIALS:
        return None

    raise FileNotFoundError(f"Gemini service account file not found: {credentials_path}")


def _project_from_service_account(credentials_path: Path | None) -> str | None:
    if credentials_path is None or not credentials_path.exists():
        return os.environ.get("GOOGLE_CLOUD_PROJECT")

    data = json.loads(credentials_path.read_text(encoding="utf-8"))
    return data.get("project_id") or os.environ.get("GOOGLE_CLOUD_PROJECT")


def _encode_jpeg(frame: Any, cv2: Any) -> bytes:
    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("Could not encode video frame as JPEG")
    return encoded.tobytes()


def _classify_frame(
    client: Any,
    types: Any,
    *,
    model: str,
    jpeg_bytes: bytes,
    timestamp_ms: int,
) -> GeminiFrameResult:
    prompt = (
        f"Classify this video frame sampled at {format_timecode(timestamp_ms)}. "
        "Use the JSON schema exactly."
    )
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    return _parse_result(response.text or "{}")


def _parse_result(text: str) -> GeminiFrameResult:
    data = json.loads(_strip_code_fence(text))
    tag = str(data.get("tag", "none")).casefold()
    tag = {
        "rain": "spray",
        "impact": "shake",
        "racing": "speed",
        "cold": "speed",
    }.get(tag, tag)
    if tag not in {"spray", "shake", "speed", "none"}:
        tag = "none"

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    reason = str(data.get("reason", ""))[:120]
    return GeminiFrameResult(tag=tag, confidence=max(0.0, min(1.0, confidence)), reason=reason)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _build_continuous_events(
    samples: list[GeminiFrameSample],
    *,
    first_index: int,
    duration_ms: int,
    interval_ms: int,
    hold_frames: int,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    active: GeminiFrameResult | None = None
    active_start_ms = 0
    active_last_seen_ms = 0
    missed_frames = 0

    for sample in samples:
        result = sample.result
        if result.tag == "none":
            if active is not None:
                missed_frames += 1
                if missed_frames > hold_frames:
                    _append_continuous_event(
                        events,
                        first_index=first_index,
                        start_ms=active_start_ms,
                        end_ms=sample.timestamp_ms,
                        result=active,
                    )
                    active = None
                    missed_frames = 0
            continue

        if active is None:
            active = result
            active_start_ms = sample.timestamp_ms
            active_last_seen_ms = sample.timestamp_ms
            missed_frames = 0
            continue

        if result.tag == active.tag:
            active = _merge_results(active, result)
            active_last_seen_ms = sample.timestamp_ms
            missed_frames = 0
            continue

        _append_continuous_event(
            events,
            first_index=first_index,
            start_ms=active_start_ms,
            end_ms=sample.timestamp_ms,
            result=active,
        )
        active = result
        active_start_ms = sample.timestamp_ms
        active_last_seen_ms = sample.timestamp_ms
        missed_frames = 0

    if active is not None:
        fallback_end_ms = active_last_seen_ms + interval_ms * (missed_frames + 1)
        end_ms = min(duration_ms, fallback_end_ms) if duration_ms > active_start_ms else fallback_end_ms
        _append_continuous_event(
            events,
            first_index=first_index,
            start_ms=active_start_ms,
            end_ms=end_ms,
            result=active,
        )

    return events


def _append_continuous_event(
    events: list[dict[str, Any]],
    *,
    first_index: int,
    start_ms: int,
    end_ms: int,
    result: GeminiFrameResult,
) -> None:
    if end_ms <= start_ms:
        return
    events.append(_build_gemini_event(first_index + len(events), start_ms, end_ms, result))


def _merge_results(left: GeminiFrameResult, right: GeminiFrameResult) -> GeminiFrameResult:
    confidence = max(left.confidence, right.confidence)
    reason = right.reason or left.reason
    return GeminiFrameResult(tag=left.tag, confidence=confidence, reason=reason)


def _build_gemini_event(
    index: int,
    start_ms: int,
    end_ms: int,
    result: GeminiFrameResult,
) -> dict[str, Any]:
    effects = {module: dict(config) for module, config in NEUTRAL_EFFECTS.items()}

    if result.tag == "spray":
        effects["mist"] = {"enabled": True}
        led = {"rgb": [115, 130, 140], "brightness": 0.45}
    elif result.tag == "shake":
        effects["vibration"] = {"enabled": True}
        led = {"rgb": [255, 60, 35], "brightness": 0.8}
    elif result.tag == "speed":
        effects["fan"] = {"enabled": True}
        led = {"rgb": [180, 210, 230], "brightness": 0.45}
    else:
        led = NEUTRAL_EFFECTS["led"]

    effects["led"] = led

    return {
        "id": f"gemini-video-{index:04d}",
        "source": "gemini_video",
        "start_ms": start_ms,
        "end_ms": end_ms,
        "start": format_timecode(start_ms),
        "end": format_timecode(end_ms),
        "duration_ms": max(0, end_ms - start_ms),
        "text": result.reason,
        "tags": [f"gemini_{result.tag}"],
        "confidence": result.confidence,
        "duration_limits": {"fan": None, "vibration": None},
        "effects": effects,
    }
