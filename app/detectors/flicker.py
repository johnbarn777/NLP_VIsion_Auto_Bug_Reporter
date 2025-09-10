from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from app.schemas.models import AnomalyEvent, FramePacket
from app.schemas.types import AnomalyType, Severity

from .base import Detector, DetectorState


@dataclass
class FlickerDetector(Detector):
    """Detect rapid luminance oscillations using a temporal FFT."""

    window: int = 8
    ratio_thresh: float = 0.6

    def process(self, pkt: FramePacket, state: DetectorState) -> Optional[AnomalyEvent]:
        img = cv2.imread(str(pkt.path))
        if img is None:
            return None

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        luma = hsv[:, :, 2]
        mean_luma = float(np.mean(luma))

        lumas = state.setdefault("luma_window", [])
        lumas.append(mean_luma)
        if len(lumas) > self.window:
            lumas.pop(0)

        if len(lumas) < self.window:
            return None

        arr = np.array(lumas, dtype=np.float32)
        arr -= np.mean(arr)

        fft = np.fft.rfft(arr)
        mags = np.abs(fft) ** 2
        total = float(np.sum(mags))
        if total <= 1e-6:
            ratio = 0.0
        else:
            ratio = float(np.sum(mags[2:]) / total)

        if ratio < self.ratio_thresh:
            return None

        event_id = state.get("next_event_id", 1)
        state["next_event_id"] = event_id + 1
        state["luma_window"] = []

        return AnomalyEvent(
            event_id=event_id,
            type=AnomalyType.FLICKER,
            severity=Severity.LOW,
            frame=pkt,
            confidence=max(0.0, min(1.0, ratio)),
            metrics={"high_freq_ratio": ratio},
            created_at=datetime.utcnow(),
        )
