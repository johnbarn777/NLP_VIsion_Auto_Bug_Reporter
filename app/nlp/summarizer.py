from app.schemas.models import AnomalyEvent, BugDraft


def summarize(event: AnomalyEvent) -> BugDraft:
    """Summarize an anomaly event into a bug draft."""
    return BugDraft(summary="", description="", event=event)
