"""Detection pipeline loading detectors from configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple, Type

import yaml

from app.schemas.models import AnomalyEvent, FramePacket

from .base import Detector, DetectorState
from .blank import BlankDetector
from .flicker import FlickerDetector
from .freeze import FreezeDetector

DetectorFactory = Type[Detector]

NAME_MAP: Dict[str, DetectorFactory] = {
    "blank": BlankDetector,
    "freeze": FreezeDetector,
    "flicker": FlickerDetector,
}


class DetectorPipeline:
    """Manage a sequence of detectors and deduplicate emitted events."""

    def __init__(self, detectors: Sequence[Detector]) -> None:
        self.detectors = list(detectors)
        self._states: List[DetectorState] = [{} for _ in self.detectors]
        # track (anomaly_type, frame_id) to avoid duplicate events
        self._seen: Set[Tuple[str, int]] = set()

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "DetectorPipeline":
        """Instantiate detectors based on a YAML configuration."""
        if path is None:
            path = Path(__file__).resolve().parent.parent / "config" / "detectors.yaml"
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh) or {}
            order = cfg.get("detectors", [])
        else:  # fallback to all known detectors
            order = list(NAME_MAP.keys())

        detectors: List[Detector] = []
        for name in order:
            factory = NAME_MAP.get(name)
            if factory is not None:
                detectors.append(factory())
        return cls(detectors)

    def process(self, pkt: FramePacket) -> List[AnomalyEvent]:
        """Run all detectors over a frame packet and return new events."""
        events: List[AnomalyEvent] = []
        for det, state in zip(self.detectors, self._states):
            evt = det.process(pkt, state)
            if evt is None:
                continue
            key = (evt.type.value, evt.frame.frame_id)
            if key in self._seen:
                continue
            self._seen.add(key)
            events.append(evt)
        return events


__all__ = ["DetectorPipeline"]
