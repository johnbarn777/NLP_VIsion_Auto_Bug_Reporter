from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class FramePacket(BaseModel):
    timestamp: datetime
    path: str


class AnomalyEvent(BaseModel):
    type: str
    frame: FramePacket
    details: Dict[str, Any] = {}


class BugDraft(BaseModel):
    summary: str
    description: str
    event: AnomalyEvent
