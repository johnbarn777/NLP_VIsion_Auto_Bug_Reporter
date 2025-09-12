from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import cv2
import numpy as np

from app.detectors.pipeline import DetectorPipeline
from app.schemas.models import FramePacket
from app.schemas.types import AnomalyType
from datasets import iterate_atari_clips, iterate_echo_clips


def _write_frames(dir_path: Path, frames: List[np.ndarray]) -> List[Path]:
    dir_path.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for i, img in enumerate(frames, start=1):
        p = dir_path / f"frame_{i:03d}.png"
        cv2.imwrite(str(p), img)
        paths.append(p)
    return paths


def _synth_blank(n: int = 5, h: int = 64, w: int = 64) -> List[np.ndarray]:
    return [np.zeros((h, w, 3), dtype=np.uint8) for _ in range(n)]


def _synth_freeze(n: int = 5, h: int = 64, w: int = 64) -> List[np.ndarray]:
    img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    return [img.copy() for _ in range(n)]


def _synth_flicker(n: int = 8, h: int = 64, w: int = 64) -> List[np.ndarray]:
    a = np.zeros((h, w, 3), dtype=np.uint8)
    b = np.full((h, w, 3), 255, dtype=np.uint8)
    frames = []
    for i in range(n):
        frames.append(a if i % 2 == 0 else b)
    return frames


def _to_packets(frames: List[Path]) -> List[FramePacket]:
    now = datetime.utcnow()
    pkts: List[FramePacket] = []
    for i, p in enumerate(frames, start=1):
        pkts.append(
            FramePacket(frame_id=i, timestamp=now + timedelta(milliseconds=40 * i), path=p)
        )
    return pkts


def _assert_detects(label: AnomalyType, frame_paths: List[Path]) -> None:
    pipeline = DetectorPipeline.from_yaml()
    pkts = _to_packets(frame_paths)
    matched = False
    for pkt in pkts:
        events = pipeline.process(pkt)
        if any(evt.type == label for evt in events):
            matched = True
            break
    assert matched, f"Expected detection for {label}"


def test_dataset_loaders_integration(tmp_path, monkeypatch):
    # Create synthetic Atari AAD root
    atari_root = tmp_path / "atari"
    _write_frames(atari_root / "blank" / "clip_1", _synth_blank())
    _write_frames(atari_root / "freeze" / "clip_1", _synth_freeze())
    _write_frames(atari_root / "flicker" / "clip_1", _synth_flicker())

    # Create synthetic Echo+ root
    echo_root = tmp_path / "echo"
    _write_frames(echo_root / "blank" / "clip_a", _synth_blank())
    _write_frames(echo_root / "freeze" / "clip_a", _synth_freeze())
    _write_frames(echo_root / "flicker" / "clip_a", _synth_flicker())

    monkeypatch.setenv("ATARI_AAD_ROOT", str(atari_root))
    monkeypatch.setenv("ECHO_PLUS_ROOT", str(echo_root))

    # Atari checks
    atari_seen = {AnomalyType.BLANK: False, AnomalyType.FREEZE: False, AnomalyType.FLICKER: False}
    for frames, label in iterate_atari_clips():
        if label in atari_seen and not atari_seen[label]:
            _assert_detects(label, frames)
            atari_seen[label] = True
    assert all(atari_seen.values()), "Did not see all expected Atari labels"

    # Echo+ checks
    echo_seen = {AnomalyType.BLANK: False, AnomalyType.FREEZE: False, AnomalyType.FLICKER: False}
    for frames, label in iterate_echo_clips():
        if label in echo_seen and not echo_seen[label]:
            _assert_detects(label, frames)
            echo_seen[label] = True
    assert all(echo_seen.values()), "Did not see all expected Echo+ labels"

