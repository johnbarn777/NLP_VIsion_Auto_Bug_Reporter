"""Data models used across the application.

These Pydantic models define the contracts between the capture, detection,
NLP and reporting layers.  They intentionally stay lightweight so they can be
serialised directly to JSON for storage or transport.
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from .types import AnomalyType, Severity

class FramePacket(BaseModel):
    """Metadata about a captured frame saved on disk."""

    frame_id: int
    timestamp: datetime
    path: Path
    checksum: Optional[str] = None

class AnomalyEvent(BaseModel):
    """A detected anomaly with accompanying context and metrics."""

    event_id: int
    type: AnomalyType
    severity: Severity
    frame: FramePacket
    confidence: float = Field(..., ge=0.0, le=1.0)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)



class BugDraft(BaseModel):
    """Draft report generated for an anomaly event."""
    event: AnomalyEvent
    title: str
    body_md: str
    attachments: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SubmissionResult(BaseModel):
    """Result from submitting a :class:`BugDraft` to an external system."""

    draft: BugDraft
    success: bool
    external_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


__all__ = [
    "FramePacket",
    "AnomalyEvent",
    "BugDraft",
    "SubmissionResult",
]
