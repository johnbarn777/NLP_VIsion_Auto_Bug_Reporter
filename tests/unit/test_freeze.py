from datetime import datetime

import cv2
import numpy as np

from app.detectors.freeze import FreezeDetector
from app.schemas.models import FramePacket
from app.schemas.types import AnomalyType


def make_packet(img: np.ndarray, tmp_path, frame_id: int) -> FramePacket:
    path = tmp_path / f"frame_{frame_id}.png"
    cv2.imwrite(str(path), img)
    return FramePacket(frame_id=frame_id, timestamp=datetime.utcnow(), path=path)


def test_freeze_detector_flags_static_sequence(tmp_path):
    det = FreezeDetector(min_frames=3, mad_thresh=1.0)
    state = {}
    img = np.zeros((32, 32, 3), dtype=np.uint8)

    evt = None
    for i in range(4):
        pkt = make_packet(img, tmp_path, i)
        evt = det.process(pkt, state)

    assert evt is not None
    assert evt.type == AnomalyType.FREEZE


def test_freeze_detector_ignores_motion(tmp_path):
    det = FreezeDetector(min_frames=3, mad_thresh=1.0)
    state = {}
    size = 32

    for i in range(5):
        img = np.zeros((size, size, 3), dtype=np.uint8)
        cv2.circle(img, (i, i), 1, (255, 255, 255), -1)
        pkt = make_packet(img, tmp_path, i)
        assert det.process(pkt, state) is None
