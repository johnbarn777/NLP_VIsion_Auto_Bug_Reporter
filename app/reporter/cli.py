"""Command-line interface for exporting bug drafts."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.reporter import exporter
from app.schemas.models import AnomalyEvent, BugDraft, FramePacket
from app.schemas.types import AnomalyType, Severity
from app.storage import db, models


def _to_draft(draft: models.Draft) -> BugDraft:
    frame_model = draft.event.frame
    frame = FramePacket(
        frame_id=frame_model.id,
        timestamp=frame_model.timestamp,
        path=Path(frame_model.path),
        checksum=frame_model.checksum,
    )
    event_model = draft.event
    event = AnomalyEvent(
        event_id=event_model.id,
        type=AnomalyType(event_model.type),
        severity=Severity(event_model.severity),
        frame=frame,
        confidence=event_model.confidence,
        metrics=event_model.metrics,
        created_at=event_model.created_at,
    )
    return BugDraft(
        event=event,
        title=draft.title,
        body_md=draft.body_md,
        attachments=draft.attachments,
        created_at=draft.created_at,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export bug drafts")
    parser.add_argument(
        "--last", type=int, default=1, help="Number of drafts to export"
    )
    parser.add_argument("--csv", action="store_true", help="Write CSV output")
    parser.add_argument("--json", action="store_true", help="Write JSON output")
    args = parser.parse_args(argv)

    if not args.csv and not args.json:
        args.csv = args.json = True

    with db.session_scope() as session:
        q = (
            session.query(models.Draft)
            .join(models.Event)
            .order_by(models.Event.created_at.desc())
            .limit(args.last)
        )
        drafts = [_to_draft(d) for d in q.all()]

    for draft in reversed(drafts):
        exporter.submit(draft, write_csv=args.csv, write_json=args.json)


if __name__ == "__main__":
    main()
