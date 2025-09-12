from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set

import cv2

from app.detectors.pipeline import DetectorPipeline
from app.nlp import summarizer
from app.schemas.models import AnomalyEvent, FramePacket
from app.schemas.types import AnomalyType
from app.storage import db, models, repo
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


def _packets(paths: List[Path], *, start_id: int = 1) -> List[FramePacket]:
    base = datetime.utcnow()
    return [
        FramePacket(
            frame_id=start_id + i,
            timestamp=base + timedelta(milliseconds=40 * i),
            path=p,
        )
        for i, p in enumerate(paths)
    ]


def _copy_with_event_id(evt: AnomalyEvent, eid: int) -> AnomalyEvent:
    # Pydantic v2: construct a new model with updated event_id
    return AnomalyEvent(
        event_id=eid,
        type=evt.type,
        severity=evt.severity,
        frame=evt.frame,
        confidence=evt.confidence,
        metrics=evt.metrics,
        created_at=evt.created_at,
    )


def test_e2e_on_synthetic_clips(tmp_path):
    # 1) Generate synthetic MP4s and ground truth
    out_dir = tmp_path / "synthetic"
    truth = generate_synthetic_anomalies(out_dir)
    files = sorted(out_dir.glob("*.mp4"))
    assert len(files) >= 3
    assert (out_dir / "ground_truth.json").exists()

    # 2) Init a fresh SQLite DB in tmp and create tables
    db_path = tmp_path / "app.db"
    # Reset globals in case prior tests touched them
    db._engine = None  # type: ignore[attr-defined]
    db._SessionLocal = None  # type: ignore[attr-defined]
    db.init_engine(f"sqlite:///{db_path}")
    models.Base.metadata.create_all(db.get_engine())

    # 3) Process frames through the detector pipeline, persist first event of each type
    pipeline = DetectorPipeline.from_yaml()
    target_types: Set[AnomalyType] = {
        AnomalyType.BLANK,
        AnomalyType.FREEZE,
        AnomalyType.FLICKER,
    }
    seen: Set[AnomalyType] = set()
    saved_event_ids: List[int] = []

    next_frame_id = 1
    next_event_id = 1

    with db.session_scope() as session:
        # Iterate over produced clips; stop early once we saw all target types
        for item in truth["clips"]:
            if seen == target_types:
                break
            video = Path(item["file"]).resolve()
            frames = _extract_frames(video, tmp_path / f"frames_{video.stem}")

            # Feed frames until we observe any new type; then continue to next clip
            for pkt in _packets(frames, start_id=next_frame_id):
                next_frame_id = pkt.frame_id + 1
                for evt in pipeline.process(pkt):
                    if evt.type in target_types and evt.type not in seen:
                        evt_u = _copy_with_event_id(evt, next_event_id)
                        next_event_id += 1

                        # Persist event and corresponding draft
                        repo.save_event(session, evt_u)
                        draft = summarizer.summarize(evt_u)
                        # Attach at least the triggering frame path for completeness
                        draft.attachments.append(str(pkt.path))
                        repo.save_draft(session, draft)

                        seen.add(evt_u.type)
                        saved_event_ids.append(evt_u.event_id)
                        break  # move to next frame/clip after capturing this type
                if seen == target_types:
                    break

    # Ensure we captured at least one of each primary type
    assert target_types.issubset(seen), f"Missing types: {target_types - seen}"

    # 4) Export via CLI to CSV + per-event JSON in a temp cwd
    from app.reporter.cli import main as cli_main

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        cli_main(["--last", str(len(saved_event_ids)), "--csv", "--json"])
    finally:
        os.chdir(cwd)
        db._engine = None  # type: ignore[attr-defined]
        db._SessionLocal = None  # type: ignore[attr-defined]

    csv_path = tmp_path / "data" / "reports.csv"
    assert csv_path.exists() and csv_path.stat().st_size > 0

    for eid in saved_event_ids:
        j = tmp_path / "data" / f"report_{eid}.json"
        assert j.exists(), f"Missing JSON export for event {eid}"
