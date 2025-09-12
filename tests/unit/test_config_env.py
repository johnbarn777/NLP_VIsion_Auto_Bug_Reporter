from datetime import datetime

import cv2
import numpy as np

from app.config.load import load_settings
from app.detectors.pipeline import DetectorPipeline
from app.detectors.freeze import FreezeDetector
from app.schemas.models import FramePacket


def make_packet(img: np.ndarray, tmp_path, frame_id: int) -> FramePacket:
    path = tmp_path / f"frame_{frame_id}.png"
    cv2.imwrite(str(path), img)
    return FramePacket(frame_id=frame_id, timestamp=datetime.utcnow(), path=path)


def test_env_override_changes_freeze_frames(monkeypatch, tmp_path):
    monkeypatch.setenv("FREEZE_FRAMES", "2")
    settings = load_settings()
    pipeline = DetectorPipeline.from_yaml(settings=settings)
    freeze_det = next(d for d in pipeline.detectors if isinstance(d, FreezeDetector))
    state = {}
    img = np.zeros((32, 32, 3), dtype=np.uint8)
    evt = None
    for i in range(3):
        pkt = make_packet(img, tmp_path, i)
        evt = freeze_det.process(pkt, state)
    assert evt is not None
