"""SQLAlchemy ORM models for persisting frames, events and drafts."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class Frame(Base):
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    events: Mapped[List["Event"]] = relationship(back_populates="frame")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    frame_id: Mapped[int] = mapped_column(ForeignKey("frames.id"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    metrics: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    frame: Mapped[Frame] = relationship(back_populates="events")
    drafts: Mapped[List["Draft"]] = relationship(back_populates="event")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body_md: Mapped[str] = mapped_column(String, nullable=False)
    attachments: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event: Mapped[Event] = relationship(back_populates="drafts")


__all__ = ["Base", "Frame", "Event", "Draft"]
