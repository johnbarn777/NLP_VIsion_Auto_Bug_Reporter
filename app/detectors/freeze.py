from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import cv2

from app.schemas.models import AnomalyEvent, FramePacket
from app.schemas.types import AnomalyType, Severity

from .base import Detector, DetectorState
from .utils import mad


@dataclass
class FreezeDetector(Detector):
    """Detect long sequences of nearly identical frames."""

    mad_thresh: float = 1.0
    min_frames: int = 3

    def process(self, pkt: FramePacket, state: DetectorState) -> Optional[AnomalyEvent]:
        img = cv2.imread(str(pkt.path))
        if img is None:
            return None

        prev = state.get("prev_frame")
        state["prev_frame"] = img

        if prev is None:
            state["freeze_run"] = 0
            return None

        diff = mad(prev, img)

        if diff < self.mad_thresh:
            state["freeze_run"] = state.get("freeze_run", 0) + 1
        else:
            state["freeze_run"] = 0

        if state.get("freeze_run", 0) < self.min_frames:
            return None

        event_id = state.get("next_event_id", 1)
        state["next_event_id"] = event_id + 1
        state["freeze_run"] = 0

        confidence = max(0.0, min(1.0, 1 - diff / self.mad_thresh))
        return AnomalyEvent(
            event_id=event_id,
            type=AnomalyType.FREEZE,
            severity=Severity.LOW,
            frame=pkt,
            confidence=confidence,
            metrics={"mad": diff},
            created_at=datetime.utcnow(),
        )
