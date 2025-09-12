from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from app.reporter import exporter
from app.schemas.models import AnomalyEvent, BugDraft, FramePacket
from app.schemas.types import AnomalyType, Severity


def _make_draft(tmp_path: Path, eid: int) -> BugDraft:
    shot = tmp_path / f"screenshot_{eid}.png"
    shot.write_text("data")
    frame = FramePacket(frame_id=eid, timestamp=datetime.utcnow(), path=shot)
    event = AnomalyEvent(
        event_id=eid,
        type=AnomalyType.BLANK,
        severity=Severity.LOW,
        frame=frame,
        confidence=0.9,
        metrics={"value": 1.0},
        created_at=datetime.utcnow(),
    )
    return BugDraft(event=event, title=f"Bug {eid}", body_md="Body", attachments=[str(shot)])


def test_exporter_writes_header_once_and_appends(tmp_path: Path, monkeypatch):
    # Redirect DATA_DIR to tmp
    monkeypatch.setattr(exporter, "DATA_DIR", tmp_path)
    monkeypatch.setattr(exporter, "CSV_PATH", tmp_path / "reports.csv")

    d1 = _make_draft(tmp_path, 1)
    d2 = _make_draft(tmp_path, 2)

    exporter.submit(d1, write_csv=True, write_json=True)
    exporter.submit(d2, write_csv=True, write_json=True)

    # CSV has header + 2 rows
    csv_path = tmp_path / "reports.csv"
    assert csv_path.exists()
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 2
    assert rows[0]["title"] == d1.title
    assert rows[1]["title"] == d2.title

    # JSON files present
    j1 = tmp_path / f"report_{d1.event.event_id}.json"
    j2 = tmp_path / f"report_{d2.event.event_id}.json"
    assert j1.exists() and j2.exists()
    data = json.loads(j1.read_text())
    assert data["title"] == d1.title

