from __future__ import annotations

import json
import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.detectors.pipeline import DetectorPipeline
from app.schemas.models import FramePacket
from app.storage import artifacts, models, repo


def make_packet(img: np.ndarray, tmp_path: Path, frame_id: int) -> FramePacket:
    path = tmp_path / f"frame_{frame_id}.png"
    cv2.imwrite(str(path), img)
    return FramePacket(frame_id=frame_id, timestamp=datetime.utcnow(), path=path)


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    models.Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_pipeline_generates_artifacts(tmp_path):
    black = np.zeros((32, 32, 3), dtype=np.uint8)
    pipeline = DetectorPipeline.from_yaml()
    events_dir = tmp_path / "events"
    artifacts_dir = tmp_path / "artifacts"

    session = make_session()
    try:
        for i in range(5):
            pkt = make_packet(black, tmp_path, i)
            for evt in pipeline.process(pkt):
                repo.save_event(session, evt)
                artifacts.save_event_artifacts(
                    evt, events_dir=events_dir, artifacts_dir=artifacts_dir
                )
        session.commit()

        stored = session.query(models.Event).all()
        assert len(stored) == 1
        event_id = stored[0].id
    finally:
        session.close()

    screenshot = events_dir / str(event_id) / "screenshot.png"
    assert screenshot.exists()

    metrics_path = artifacts_dir / "metrics.json"
    data = json.loads(metrics_path.read_text())
    assert str(event_id) in data
