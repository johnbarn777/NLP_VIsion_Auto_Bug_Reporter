import csv
import json
from pathlib import Path
from typing import Iterable

from app.schemas.models import BugDraft


def submit(drafts: Iterable[BugDraft], output: Path) -> None:
    """Export bug drafts to CSV or JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".json":
        data = [d.model_dump() for d in drafts]
        output.write_text(json.dumps(data, indent=2))
    elif output.suffix == ".csv":
        drafts = list(drafts)
        if not drafts:
            return
        with output.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=drafts[0].model_dump().keys())
            writer.writeheader()
            for d in drafts:
                writer.writerow(d.model_dump())
    else:
        raise ValueError(f"Unsupported format: {output.suffix}")
