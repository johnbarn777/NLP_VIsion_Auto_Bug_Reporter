"""Ensure schema models and enums can be imported and instantiated."""

from datetime import datetime

from app.schemas import (
    AnomalyEvent,
    BugDraft,
    FramePacket,
    SubmissionResult,
    AnomalyType,
    Severity,
)


def test_schema_roundtrip():
    """Trivial smoke test to ensure models can be instantiated."""

    frame = FramePacket(frame_id=1, timestamp=datetime.utcnow(), path="frame.png")
    event = AnomalyEvent(
        event_id=1,
        type=AnomalyType.BLANK,
        severity=Severity.LOW,
        frame=frame,
        confidence=0.5,
    )
    draft = BugDraft(event=event, title="Bug", body_md="Markdown body")
    result = SubmissionResult(draft=draft, success=True)
    assert result.success is True