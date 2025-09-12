from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from app.reporter.cli import main
from app.schemas.models import AnomalyEvent, BugDraft, FramePacket
from app.schemas.types import AnomalyType, Severity
from app.storage import db, models, repo


def _make_draft(tmp_path: Path) -> BugDraft:
    shot = tmp_path / "s.png"
    shot.write_text("data")
    frame = FramePacket(frame_id=1, timestamp=datetime.utcnow(), path=shot)
    event = AnomalyEvent(
        event_id=1,
        type=AnomalyType.BLANK,
        severity=Severity.LOW,
        frame=frame,
        confidence=0.9,
        metrics={"value": 1.0},
        created_at=datetime.utcnow(),
    )
    return BugDraft(event=event, title="Bug", body_md="Body", attachments=[str(shot)])


def test_cli_defaults_export_both(tmp_path, monkeypatch):
    # Fresh DB
    db_path = tmp_path / "app.db"
    db._engine = None  # type: ignore[attr-defined]
    db._SessionLocal = None  # type: ignore[attr-defined]
    db.init_engine(f"sqlite:///{db_path}")
    models.Base.metadata.create_all(db.get_engine())

    draft = _make_draft(tmp_path)
    with db.session_scope() as session:
        repo.save_draft(session, draft)

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # No --csv/--json flags should default to both
        main(["--last", "1"])  # defaults in CLI set both True
    finally:
        os.chdir(cwd)
        db._engine = None  # type: ignore[attr-defined]
        db._SessionLocal = None  # type: ignore[attr-defined]

    assert (tmp_path / "data" / "reports.csv").exists()
    assert (tmp_path / "data" / f"report_{draft.event.event_id}.json").exists()
