from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.schemas.models import AnomalyEvent, FramePacket
from app.schemas.types import AnomalyType, Severity
from app.storage import artifacts


def _event_for_path(path: Path, eid: int = 1) -> AnomalyEvent:
    frame = FramePacket(frame_id=eid, timestamp=datetime.utcnow(), path=path)
    return AnomalyEvent(
        event_id=eid,
        type=AnomalyType.BLANK,
        severity=Severity.LOW,
        frame=frame,
        confidence=0.9,
        metrics={"k": 1.0},
        created_at=datetime.utcnow(),
    )


def test_artifacts_copy_screenshot_when_cv2_missing(tmp_path, monkeypatch):
    # Prepare a fake frame file
    src = tmp_path / "frame.png"
    src.write_bytes(b"img")

    # Force cv2 to None to exercise fallback path
    monkeypatch.setattr(artifacts, "cv2", None)

    evt = _event_for_path(src, 42)
    out_dir = artifacts.save_event_artifacts(evt, events_dir=tmp_path / "events", artifacts_dir=tmp_path / "artifacts")

    shot = out_dir / "screenshot.png"
    assert shot.exists()
    assert shot.read_bytes() == b"img"  # copied

    # Metrics file contains our event id
    metrics_path = (tmp_path / "artifacts" / "metrics.json")
    data = json.loads(metrics_path.read_text())
    assert "42" in data
    assert data["42"]["k"] == 1.0

