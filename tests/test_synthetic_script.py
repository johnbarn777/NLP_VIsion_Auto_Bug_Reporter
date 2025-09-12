from __future__ import annotations

from pathlib import Path
from typing import List

import cv2

from app.detectors.blank import BlankDetector
from app.detectors.freeze import FreezeDetector
from app.detectors.flicker import FlickerDetector
from app.detectors.pipeline import DetectorPipeline
from app.schemas.models import FramePacket
from app.schemas.types import AnomalyType
from scripts.generate_synthetic_anomalies import generate_synthetic_anomalies


def _extract_frames(video_path: Path, out_dir: Path) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open {video_path}")
    idx = 0
    paths: List[Path] = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            idx += 1
            p = out_dir / f"frame_{idx:03d}.png"
            cv2.imwrite(str(p), frame)
            paths.append(p)
    finally:
        cap.release()
    return paths


from datetime import datetime, timedelta


def _packets(paths: List[Path]) -> List[FramePacket]:
    base = datetime.utcnow()
    return [
        FramePacket(
            frame_id=i + 1, timestamp=base + timedelta(milliseconds=40 * i), path=p
        )
        for i, p in enumerate(paths)
    ]


def _precision_for_label(label: AnomalyType, frames: List[Path]) -> float:
    # Use only the corresponding detector to approximate precision cleanly
    if label == AnomalyType.BLANK:
        dets = [BlankDetector()]
    elif label == AnomalyType.FREEZE:
        dets = [FreezeDetector()]
    elif label == AnomalyType.FLICKER:
        dets = [FlickerDetector()]
    else:
        # Not testing HUD glitch here
        return 1.0

    pipe = DetectorPipeline(dets)
    total = 0
    correct = 0
    for pkt in _packets(frames):
        events = pipe.process(pkt)
        for evt in events:
            total += 1
            if evt.type == label:
                correct += 1
    if total == 0:
        return 0.0
    return correct / total


def test_script_generates_mp4s_and_detectors_are_precise(tmp_path):
    out_dir = tmp_path / "synthetic"
    truth = generate_synthetic_anomalies(out_dir)

    # Generated files
    files = list(out_dir.glob("*.mp4"))
    assert len(files) == 3, "Expected 3 MP4 files"
    assert (out_dir / "ground_truth.json").exists()

    # Evaluate precision per clip
    label_map = {
        "blank": AnomalyType.BLANK,
        "freeze": AnomalyType.FREEZE,
        "flicker": AnomalyType.FLICKER,
    }

    for item in truth["clips"]:
        video = Path(item["file"])  # absolute path from generator
        assert video.exists()
        frames = _extract_frames(video, out_dir / f"frames_{video.stem}")
        prec = _precision_for_label(label_map[item["label"]], frames)
        assert prec >= 0.8, f"Precision {prec:.2f} for {item['label']} below 0.8"
