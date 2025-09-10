from datetime import datetime

import cv2
import numpy as np

from app.detectors.blank import BlankDetector
from app.schemas.models import FramePacket
from app.schemas.types import AnomalyType


def make_packet(img: np.ndarray, tmp_path, frame_id: int) -> FramePacket:
    path = tmp_path / f"frame_{frame_id}.png"
    cv2.imwrite(str(path), img)
    return FramePacket(frame_id=frame_id, timestamp=datetime.utcnow(), path=path)


def test_blank_detector_flags_black_sequence(tmp_path):
    det = BlankDetector(min_frames=3, pct=0.99)
    state = {}
    almost_black = np.full((32, 32, 3), 5, dtype=np.uint8)

    evt = None
    for i in range(3):
        pkt = make_packet(almost_black, tmp_path, i)
        evt = det.process(pkt, state)

    assert evt is not None
    assert evt.type == AnomalyType.BLANK


def test_blank_detector_low_fp_on_dark_frames(tmp_path):
    det = BlankDetector(min_frames=3, pct=0.99)
    state = {}
    dark = np.full((32, 32, 3), 40, dtype=np.uint8)

    for i in range(5):
        pkt = make_packet(dark, tmp_path, i)
        assert det.process(pkt, state) is None
