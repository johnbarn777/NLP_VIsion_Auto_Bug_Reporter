from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.schemas.models import AnomalyEvent, FramePacket

DetectorState = Dict[str, Any]


class Detector(ABC):
    """Base interface for frame anomaly detectors."""

    @abstractmethod
    def process(self, pkt: FramePacket, state: DetectorState) -> Optional[AnomalyEvent]:
        """Process a frame packet and return an anomaly event if detected."""


__all__ = ["Detector", "DetectorState"]
