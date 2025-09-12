from __future__ import annotations

from typing import Dict

from app.config.load import load_settings
from app.schemas.models import AnomalyEvent, BugDraft
from .templates import DEFAULT_TEMPLATE, TEMPLATES


_SETTINGS = load_settings()


def _environment_context() -> str:
    """Compose a small environment string from config settings."""
    fps = getattr(_SETTINGS, "fps", None)
    buffer_s = getattr(_SETTINGS, "buffer_seconds", None)
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
