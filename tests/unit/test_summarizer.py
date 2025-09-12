from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.nlp.summarizer as summarizer
from app.schemas.models import AnomalyEvent, FramePacket
from app.schemas.types import AnomalyType, Severity
from app.storage import models, repo


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    models.Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def sample_event(
    anomaly_type: Enum = AnomalyType.BLANK,
    metrics: dict | None = None,
    severity: Severity = Severity.LOW,
) -> AnomalyEvent:
    frame = FramePacket(
        frame_id=1, timestamp=datetime.utcnow(), path=Path("/tmp/frame.png")
    )
    return AnomalyEvent(
        event_id=1,
        type=anomaly_type,
        severity=severity,
        frame=frame,
        confidence=0.9,
        metrics={"value": 1.0} if metrics is None else metrics,
        created_at=datetime.utcnow(),
    )


@pytest.mark.parametrize(
    "atype,title,observed",
    [
        (
            AnomalyType.BLANK,
            "Blank Screen Detected",
            "Game rendered a blank screen.",
        ),
        (
            AnomalyType.FREEZE,
            "Freeze Detected",
            "Gameplay appeared frozen.",
        ),
        (
            AnomalyType.FLICKER,
            "Flicker Detected",
            "Rapid brightness changes observed.",
        ),
        (
            AnomalyType.HUD_GLITCH,
            "HUD Glitch Detected",
            "HUD elements appeared corrupted.",
        ),
    ],
)
def test_summarize_renders_template_for_types(atype, title, observed):
    event = sample_event(anomaly_type=atype, metrics={"value": 1.0})
    draft = summarizer.summarize(event)

    assert draft.title == title
    assert observed in draft.body_md
    assert "**Environment**: fps=5, buffer=5s" in draft.body_md
    assert "- value: 1.0" in draft.body_md


def test_summarize_handles_missing_metrics():
    event = sample_event(metrics={})
    draft = summarizer.summarize(event)
    assert "## Metrics\nnone" in draft.body_md


def test_summarize_uses_default_template_for_unknown_type(monkeypatch):
    monkeypatch.setattr(summarizer, "TEMPLATES", {})
    event = sample_event(anomaly_type=AnomalyType.BLANK)
    draft = summarizer.summarize(event)

    assert draft.title == "Blank Anomaly Detected"
    assert "# Blank Anomaly Detected" in draft.body_md


def test_summarize_persists_draft_to_db():
    event = sample_event()
    draft = summarizer.summarize(event)

    with make_session() as session:
        repo.save_draft(session, draft)
        stored = session.query(models.Draft).one()

        assert stored.title == draft.title
        assert stored.body_md == draft.body_md
