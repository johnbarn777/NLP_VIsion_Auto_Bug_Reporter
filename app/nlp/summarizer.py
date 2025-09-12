from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml

from app.schemas.models import AnomalyEvent, BugDraft
from .templates import DEFAULT_TEMPLATE, TEMPLATES

# Load simple context from config/settings.yaml
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"


def _load_settings(path: Path) -> Dict[str, object]:
    if path.exists():
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {}


_SETTINGS = _load_settings(_CONFIG_PATH)


def _environment_context() -> str:
    """Compose a small environment string from config settings."""
    fps = _SETTINGS.get("fps")
    buffer_s = _SETTINGS.get("buffer_seconds")
    parts = []
    if fps is not None:
        parts.append(f"fps={fps}")
    if buffer_s is not None:
        parts.append(f"buffer={buffer_s}s")
    return ", ".join(parts)


def _metrics_to_md(metrics: Dict[str, object]) -> str:
    if not metrics:
        return "none"
    return "\n".join(f"- {k}: {v}" for k, v in metrics.items())


def summarize(event: AnomalyEvent) -> BugDraft:
    """Summarize an anomaly event into a :class:`BugDraft`."""

    template = TEMPLATES.get(event.type, DEFAULT_TEMPLATE)
    env = _environment_context()
    metrics_md = _metrics_to_md(event.metrics)
    event_type = event.type.value.replace("_", " ").title()

    title = template.title.format(event_type=event_type)
    body_md = template.body.format(
        severity=event.severity.value,
        environment=env,
        metrics_md=metrics_md,
        event_type=event_type,
    )
    return BugDraft(event=event, title=title, body_md=body_md)
