from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.schemas.models import AnomalyEvent, BugDraft, FramePacket
from app.schemas.types import AnomalyType, Severity
from app.storage import models, repo


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    models.Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def sample_event() -> AnomalyEvent:
    frame = FramePacket(frame_id=1, timestamp=datetime.utcnow(), path=Path("/tmp/frame.png"))
    return AnomalyEvent(
        event_id=1,
        type=AnomalyType.BLANK,
        severity=Severity.LOW,
        frame=frame,
        confidence=0.9,
        metrics={"value": 1.0},
        created_at=datetime.utcnow(),
    )


def test_save_event_and_list_events():
    event = sample_event()
    with make_session() as session:
        repo.save_event(session, event)
        events = repo.list_events(session)
        assert len(events) == 1
        stored = events[0]
        assert stored.id == event.event_id
        assert stored.frame.path == str(event.frame.path)


def test_save_draft():
    event = sample_event()
    draft = BugDraft(event=event, title="Title", body_md="Body", attachments=["a.png"])
    with make_session() as session:
        repo.save_draft(session, draft)
        stored = session.query(models.Draft).one()
        assert stored.title == draft.title
        assert stored.event.id == event.event_id
