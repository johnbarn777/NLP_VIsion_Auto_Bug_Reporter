"""Common type definitions used by schema models."""

from enum import Enum


class AnomalyType(str, Enum):
    """Supported anomaly categories detected in gameplay."""

    BLANK = "blank"
    FREEZE = "freeze"
    FLICKER = "flicker"
    HUD_GLITCH = "hud_glitch"


class Severity(str, Enum):
    """Severity levels for detected anomalies and bug reports."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


__all__ = ["AnomalyType", "Severity"]
