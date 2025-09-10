from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import cv2

from app.schemas.models import AnomalyEvent, FramePacket
from app.schemas.types import AnomalyType, Severity

from .base import Detector, DetectorState


@dataclass
class BlankDetector(Detector):
    """Detect long sequences of nearly black frames."""

    luma_thresh: int = 10
    sat_thresh: int = 15
    pct: float = 0.95
    min_frames: int = 3

    def process(self, pkt: FramePacket, state: DetectorState) -> Optional[AnomalyEvent]:
        img = cv2.imread(str(pkt.path))
        if img is None:
            return None

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        luma = hsv[:, :, 2]

        l_hist = cv2.calcHist([luma], [0], None, [256], [0, 256])
        s_hist = cv2.calcHist([sat], [0], None, [256], [0, 256])

        l_ratio = float(l_hist[: self.luma_thresh + 1].sum() / l_hist.sum())
        s_ratio = float(s_hist[: self.sat_thresh + 1].sum() / s_hist.sum())

        if l_ratio >= self.pct and s_ratio >= self.pct:
            state["blank_run"] = state.get("blank_run", 0) + 1
        else:
            state["blank_run"] = 0

        if state.get("blank_run", 0) < self.min_frames:
            return None

        event_id = state.get("next_event_id", 1)
        state["next_event_id"] = event_id + 1
        state["blank_run"] = 0

        confidence = min(l_ratio, s_ratio)
        return AnomalyEvent(
            event_id=event_id,
            type=AnomalyType.BLANK,
            severity=Severity.LOW,
            frame=pkt,
            confidence=confidence,
            metrics={"luma_ratio": l_ratio, "sat_ratio": s_ratio},
            created_at=datetime.utcnow(),
        )
