"""Repository helpers for persisting and querying domain models."""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.schemas.models import AnomalyEvent, BugDraft, FramePacket

from . import models


def save_frame(session: Session, packet: FramePacket) -> models.Frame:
    """Persist a :class:`FramePacket` to the database."""
    frame = session.get(models.Frame, packet.frame_id)
    if frame is None:
        frame = models.Frame(
            id=packet.frame_id,
            timestamp=packet.timestamp,
            path=str(packet.path),
            checksum=packet.checksum,
        )
        session.add(frame)
    else:
        frame.timestamp = packet.timestamp
        frame.path = str(packet.path)
        frame.checksum = packet.checksum
    session.commit()
    return frame


def save_event(session: Session, event: AnomalyEvent) -> models.Event:
    """Persist an :class:`AnomalyEvent` and its frame."""
    frame = save_frame(session, event.frame)
    db_event = session.get(models.Event, event.event_id)
    if db_event is None:
        db_event = models.Event(
            id=event.event_id,
            type=event.type.value,
            severity=event.severity.value,
            frame_id=frame.id,
            confidence=event.confidence,
            metrics=event.metrics,
            created_at=event.created_at,
        )
        session.add(db_event)
    else:
        db_event.type = event.type.value
        db_event.severity = event.severity.value
        db_event.frame_id = frame.id
        db_event.confidence = event.confidence
        db_event.metrics = event.metrics
        db_event.created_at = event.created_at
    session.commit()
    return db_event


def save_draft(session: Session, draft: BugDraft) -> models.Draft:
    """Persist a :class:`BugDraft` and ensure its event exists."""
    event = save_event(session, draft.event)
    db_draft = session.query(models.Draft).filter_by(event_id=event.id).one_or_none()
    if db_draft is None:
        db_draft = models.Draft(
            event_id=event.id,
            title=draft.title,
            body_md=draft.body_md,
            attachments=draft.attachments,
            created_at=draft.created_at,
        )
        session.add(db_draft)
    else:
        db_draft.title = draft.title
        db_draft.body_md = draft.body_md
        db_draft.attachments = draft.attachments
        db_draft.created_at = draft.created_at
    session.commit()
    return db_draft


def list_events(session: Session) -> List[models.Event]:
    """Return all stored events."""
    return session.query(models.Event).all()


__all__ = ["save_frame", "save_event", "save_draft", "list_events"]
