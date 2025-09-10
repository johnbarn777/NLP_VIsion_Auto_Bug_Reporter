from datetime import datetime

import cv2
import numpy as np

from app.detectors.flicker import FlickerDetector
from app.schemas.models import FramePacket
from app.schemas.types import AnomalyType


def make_packet(img: np.ndarray, tmp_path, frame_id: int) -> FramePacket:
    path = tmp_path / f"frame_{frame_id}.png"
    cv2.imwrite(str(path), img)
    return FramePacket(frame_id=frame_id, timestamp=datetime.utcnow(), path=path)


def test_flicker_detector_flags_alternating_frames(tmp_path):
    det = FlickerDetector(window=8, ratio_thresh=0.6)
    state = {}
    bright = np.full((32, 32, 3), 255, dtype=np.uint8)
    dark = np.zeros((32, 32, 3), dtype=np.uint8)

    evt = None
    for i in range(8):
        img = bright if i % 2 == 0 else dark
        pkt = make_packet(img, tmp_path, i)
        evt = det.process(pkt, state)

    assert evt is not None
    assert evt.type == AnomalyType.FLICKER


def test_flicker_detector_ignores_luma_ramp(tmp_path):
    det = FlickerDetector(window=8, ratio_thresh=0.6)
    state = {}

    for i in range(8):
        val = int(i * 255 / 7)
        img = np.full((32, 32, 3), val, dtype=np.uint8)
        pkt = make_packet(img, tmp_path, i)
        assert det.process(pkt, state) is None
