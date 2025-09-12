import csv
import json
from pathlib import Path

from app.schemas.models import BugDraft


DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "reports.csv"


def _ensure_csv_header(path: Path, sample: BugDraft) -> None:
    """Write a header row to *path* if it does not yet exist."""
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=sample.model_dump().keys())
        writer.writeheader()


def submit(draft: BugDraft, *, write_csv: bool = True, write_json: bool = True) -> None:
    """Persist *draft* to ``/data`` as CSV row and/or JSON file."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if write_csv:
        _ensure_csv_header(CSV_PATH, draft)
        with CSV_PATH.open("a", newline="") as fh:
            data = draft.model_dump(mode="json")
            writer = csv.DictWriter(fh, fieldnames=data.keys())
            writer.writerow(data)

    if write_json:
        json_path = DATA_DIR / f"report_{draft.event.event_id}.json"
        json_path.write_text(json.dumps(draft.model_dump(mode="json"), indent=2))


__all__ = ["submit"]
