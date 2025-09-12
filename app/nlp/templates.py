from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.schemas.types import AnomalyType


@dataclass
class Template:
    """Simple container for title and body templates."""

    title: str
    body: str


TEMPLATES: Dict[AnomalyType, Template] = {
    AnomalyType.BLANK: Template(
        title="Blank Screen Detected",
        body=(
            "# Blank Screen Detected\n"
            "**Severity**: {severity}\n"
            "**Environment**: {environment}\n\n"
            "## Observed\n"
            "Game rendered a blank screen.\n\n"
            "## Expected\n"
            "Normal gameplay visuals.\n\n"
            "## Metrics\n"
            "{metrics_md}\n"
        ),
    ),
    AnomalyType.FREEZE: Template(
        title="Freeze Detected",
        body=(
            "# Freeze Detected\n"
            "**Severity**: {severity}\n"
            "**Environment**: {environment}\n\n"
            "## Observed\n"
            "Gameplay appeared frozen.\n\n"
            "## Expected\n"
            "Smooth continuous motion.\n\n"
            "## Metrics\n"
            "{metrics_md}\n"
        ),
    ),
    AnomalyType.FLICKER: Template(
        title="Flicker Detected",
        body=(
            "# Flicker Detected\n"
            "**Severity**: {severity}\n"
            "**Environment**: {environment}\n\n"
            "## Observed\n"
            "Rapid brightness changes observed.\n\n"
            "## Expected\n"
            "Stable lighting and colours.\n\n"
            "## Metrics\n"
            "{metrics_md}\n"
        ),
    ),
    AnomalyType.HUD_GLITCH: Template(
        title="HUD Glitch Detected",
        body=(
            "# HUD Glitch Detected\n"
            "**Severity**: {severity}\n"
            "**Environment**: {environment}\n\n"
            "## Observed\n"
            "HUD elements appeared corrupted.\n\n"
            "## Expected\n"
            "Correct and stable HUD rendering.\n\n"
            "## Metrics\n"
            "{metrics_md}\n"
        ),
    ),
}

DEFAULT_TEMPLATE = Template(
    title="{event_type} Anomaly Detected",
    body=(
        "# {event_type} Anomaly Detected\n"
        "**Severity**: {severity}\n"
        "**Environment**: {environment}\n\n"
        "## Metrics\n"
        "{metrics_md}\n"
    ),
)

__all__ = ["Template", "TEMPLATES", "DEFAULT_TEMPLATE"]
