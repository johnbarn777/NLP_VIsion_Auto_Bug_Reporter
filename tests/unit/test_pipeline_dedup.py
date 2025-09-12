from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.detectors.blank import BlankDetector
from app.detectors.pipeline import DetectorPipeline
from app.schemas.models import FramePacket


def _make_frame(path: Path, val: int = 0) -> None:
    img = np.full((16, 16, 3), val, dtype=np.uint8)
    cv2.imwrite(str(path), img)


def test_pipeline_deduplicates_same_event_from_multiple_detectors(tmp_path):
    # Two blank detectors in the same pipeline; both will detect on the same frame sequence
    dets = [
        BlankDetector(min_frames=1, pct=0.99),
        BlankDetector(min_frames=1, pct=0.99),
    ]
    pipeline = DetectorPipeline(dets)

    # Write one almost-black frame (min_frames=1 so immediate detection)
    fpath = tmp_path / "f.png"
    _make_frame(fpath, 5)
    pkt = FramePacket(frame_id=1, timestamp=datetime.utcnow(), path=fpath)

    events = pipeline.process(pkt)
    # Without dedup we'd have two events; expect only one
    assert len(events) == 1
