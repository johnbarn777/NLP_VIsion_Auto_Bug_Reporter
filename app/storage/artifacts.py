"""Utilities for persisting event artifacts to disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from shutil import copyfile

try:  # pragma: no cover - optional dependency
    import cv2  # type: ignore
except Exception:  # pragma: no cover - executed when OpenCV unavailable
    cv2 = None

from app.schemas.models import AnomalyEvent


def save_event_artifacts(
    event: AnomalyEvent,
    pre: Sequence[Path] | None = None,
    post: Sequence[Path] | None = None,
    events_dir: Path | None = None,
    artifacts_dir: Path | None = None,
    fps: int = 5,
) -> Path:
    """Persist screenshot, metrics and a short clip for an event.

    Args:
        event: The anomaly event being stored.
        pre: Paths to frames before the event.
        post: Paths to frames after the event.
        events_dir: Root directory for per-event folders.
        artifacts_dir: Directory for global artifact files.
        fps: Frame rate for the stitched clip.

    Returns:
        The directory where event artifacts were saved.
    """

    pre_paths = list(pre or [])
    post_paths = list(post or [])
    events_root = events_dir or Path("events")
    artifacts_root = artifacts_dir or Path("artifacts")
    events_root.mkdir(parents=True, exist_ok=True)
    artifacts_root.mkdir(parents=True, exist_ok=True)

    event_dir = events_root / str(event.event_id)
    event_dir.mkdir(parents=True, exist_ok=True)

    # screenshot
    screenshot = event_dir / "screenshot.png"
    if cv2 is not None:
        img = cv2.imread(str(event.frame.path))
        if img is not None:
            cv2.imwrite(str(screenshot), img)
    else:  # pragma: no cover - executed if OpenCV missing
        copyfile(event.frame.path, screenshot)

    # metrics
    metrics_path = artifacts_root / "metrics.json"
    metrics: dict[str, object] = {}
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text())
        except Exception:  # pragma: no cover - corrupted file
            metrics = {}
    metrics[str(event.event_id)] = event.metrics
    metrics_path.write_text(json.dumps(metrics))

    # clip
    clip_frames = pre_paths + [event.frame.path] + post_paths
    if cv2 is not None and clip_frames:
        first = cv2.imread(str(clip_frames[0]))
        if first is not None:
            height, width, _ = first.shape
            clip_path = event_dir / "clip.mp4"
            writer = cv2.VideoWriter(
                str(clip_path),
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height),
            )
            for path in clip_frames:
                frame = cv2.imread(str(path))
                if frame is not None:
                    writer.write(frame)
            writer.release()

    return event_dir


__all__ = ["save_event_artifacts"]
