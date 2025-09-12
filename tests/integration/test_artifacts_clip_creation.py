from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.schemas.models import AnomalyEvent, FramePacket
from app.schemas.types import AnomalyType, Severity
from app.storage import artifacts


def _img(val: int = 0) -> np.ndarray:
    return np.full((32, 32, 3), val, dtype=np.uint8)


def test_artifacts_creates_clip_with_cv2(tmp_path: Path):
    # Create an event frame and some pre/post frames
    event_img = _img(128)
    event_path = tmp_path / "event.png"
    cv2.imwrite(str(event_path), event_img)

    pre = []
    post = []
    for i, v in enumerate([0, 32], start=1):
        p = tmp_path / f"pre_{i}.png"
        cv2.imwrite(str(p), _img(v))
        pre.append(p)
    for i, v in enumerate([196, 255], start=1):
        p = tmp_path / f"post_{i}.png"
        cv2.imwrite(str(p), _img(v))
        post.append(p)

    evt = AnomalyEvent(
        event_id=1,
        type=AnomalyType.BLANK,
        severity=Severity.LOW,
        frame=FramePacket(frame_id=1, timestamp=datetime.utcnow(), path=event_path),
        confidence=0.9,
        metrics={"m": 1.0},
        created_at=datetime.utcnow(),
    )

    out_dir = artifacts.save_event_artifacts(
        evt,
        pre=pre,
        post=post,
        events_dir=tmp_path / "events",
        artifacts_dir=tmp_path / "artifacts",
        fps=5,
    )

    clip = out_dir / "clip.mp4"
    screenshot = out_dir / "screenshot.png"
    assert screenshot.exists()
    assert clip.exists() and clip.stat().st_size > 0
