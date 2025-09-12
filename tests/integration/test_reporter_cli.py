from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from app.reporter.cli import main
from app.schemas.models import AnomalyEvent, BugDraft, FramePacket
from app.schemas.types import AnomalyType, Severity
from app.storage import db, models, repo


def make_draft(tmp_path: Path) -> BugDraft:
    shot = tmp_path / "screenshot.png"
    shot.write_text("data")
    frame = FramePacket(
        frame_id=1,
        timestamp=datetime.utcnow(),
        path=shot,
    )
    event = AnomalyEvent(
        event_id=1,
        type=AnomalyType.BLANK,
        severity=Severity.LOW,
        frame=frame,
        confidence=0.9,
        metrics={"value": 1.0},
        created_at=datetime.utcnow(),
    )
    return BugDraft(
        event=event,
        title="Bug",
        body_md="Body",
        attachments=[str(shot)],
        created_at=datetime.utcnow(),
    )


def test_cli_exports_draft(tmp_path, monkeypatch):
    db_path = tmp_path / "app.db"
    db._engine = None  # reset globals
    db._SessionLocal = None
    db.init_engine(f"sqlite:///{db_path}")
    models.Base.metadata.create_all(db.get_engine())

    draft = make_draft(tmp_path)
    with db.session_scope() as session:
        repo.save_draft(session, draft)

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        main(["--last", "1", "--csv", "--json"])
    finally:
        os.chdir(cwd)
        db._engine = None
        db._SessionLocal = None

    csv_path = tmp_path / "data" / "reports.csv"
    json_path = tmp_path / "data" / f"report_{draft.event.event_id}.json"

    assert csv_path.exists()
    assert json_path.exists()

    rows = csv_path.read_text().strip().splitlines()
    assert len(rows) == 2  # header + one record

    data = json.loads(json_path.read_text())
    assert data["attachments"] == draft.attachments
