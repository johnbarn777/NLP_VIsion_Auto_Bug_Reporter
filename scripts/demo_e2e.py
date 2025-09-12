from __future__ import annotations

"""End-to-end demo: generate synthetic clips, detect, summarize, export.

Usage:
  poetry run python scripts/demo_e2e.py --out data/synthetic

This will:
  - Generate small MP4 clips with blank/freeze/flicker anomalies.
  - Run DetectorPipeline over frames and persist first event per type.
  - Summarize to drafts, save artifacts (screenshot/clip), export CSV/JSON.
"""

import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Set

import cv2

from app.detectors.pipeline import DetectorPipeline
from app.nlp import summarizer
from app.schemas.models import AnomalyEvent, BugDraft, FramePacket
from app.schemas.types import AnomalyType
from app.storage import artifacts as art
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


def _packets(paths: Iterable[Path], *, start_id: int = 1) -> List[FramePacket]:
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
    return AnomalyEvent(
        event_id=eid,
        type=evt.type,
        severity=evt.severity,
        frame=evt.frame,
        confidence=evt.confidence,
        metrics=evt.metrics,
        created_at=evt.created_at,
    )


def run_demo(
    out_dir: Path,
    *,
    export_csv: bool,
    export_json: bool,
    all_events: bool,
) -> None:
    # 0) Ensure base dirs
    Path("data").mkdir(parents=True, exist_ok=True)

    # 1) Generate synthetic MP4s
    truth = generate_synthetic_anomalies(out_dir)
    print(f"Generated clips in: {out_dir}")

    # 2) Init DB and create tables if missing
    db.init_engine()  # default sqlite:///./data/app.db
    models.Base.metadata.create_all(db.get_engine())

    # Determine next IDs to avoid collisions across runs
    try:
        from sqlalchemy import func

        with db.session_scope() as session:
            max_eid = session.query(func.max(models.Event.id)).scalar() or 0
            max_fid = session.query(func.max(models.Frame.id)).scalar() or 0
    except Exception:
        max_eid = 0
        max_fid = 0

    next_event_id = int(max_eid) + 1
    next_frame_id = int(max_fid) + 1

    # 3) Pipeline
    pipeline = DetectorPipeline.from_yaml()
    target_types: Set[AnomalyType] = {
        AnomalyType.BLANK,
        AnomalyType.FREEZE,
        AnomalyType.FLICKER,
    }
    seen: Set[AnomalyType] = set()
    saved_eids: List[int] = []

    # 4) Process and persist
    with db.session_scope() as session:
        for item in truth["clips"]:
            video = Path(item["file"]).resolve()
            frames = _extract_frames(video, out_dir / f"frames_{video.stem}")
            for pkt in _packets(frames, start_id=next_frame_id):
                next_frame_id = pkt.frame_id + 1
                for evt in pipeline.process(pkt):
                    if not all_events:
                        if evt.type in seen:
                            continue
                    evt_u = _copy_with_event_id(evt, next_event_id)
                    next_event_id += 1

                    repo.save_event(session, evt_u)
                    # Save artifacts (screenshot + small clip)
                    evt_dir = art.save_event_artifacts(evt_u)
                    attachments = [str(evt_dir / "screenshot.png")]
                    clip_path = evt_dir / "clip.mp4"
                    if clip_path.exists():
                        attachments.append(str(clip_path))

                    draft: BugDraft = summarizer.summarize(evt_u)
                    draft.attachments.extend(attachments)
                    repo.save_draft(session, draft)

                    # Export
                    from app.reporter import exporter

                    exporter.submit(draft, write_csv=export_csv, write_json=export_json)

                    saved_eids.append(evt_u.event_id)
                    seen.add(evt_u.type)
                    if not all_events and seen == target_types:
                        break
                if not all_events and seen == target_types:
                    break

    # 5) Summary
    data_dir = Path("data")
    print(f"Saved events: {saved_eids}")
    if export_csv:
        print(f"CSV: {data_dir / 'reports.csv'}")
    if export_json:
        for eid in saved_eids:
            print(f"JSON: {data_dir / f'report_{eid}.json'}")
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E2E demo on synthetic clips")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data") / "synthetic",
        help="Output directory for generated clips",
    )
    parser.add_argument("--csv", action="store_true", help="Write CSV export")
    parser.add_argument("--json", action="store_true", help="Write per-event JSON")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Persist/export every detected event (default: first per type)",
    )
    args = parser.parse_args()

    export_csv = args.csv
    export_json = args.json
    if not export_csv and not export_json:
        export_csv = export_json = True

    run_demo(
        args.out, export_csv=export_csv, export_json=export_json, all_events=args.all
    )


if __name__ == "__main__":
    main()
