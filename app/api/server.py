"""FastAPI server exposing events, drafts and media for a local dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parents[2]
EVENTS_DIR = BASE_DIR / "events"
DRAFTS_DIR = BASE_DIR / "drafts"
MEDIA_DIR = BASE_DIR / "media"

app = FastAPI(title="FC25 Bug Reporter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow requests from local dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json_files(directory: Path) -> list[dict]:
    """Return JSON content from all ``*.json`` files in ``directory``.

    Missing directories return an empty list.
    """
    items: list[dict] = []
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            try:
                items.append(json.loads(path.read_text()))
            except Exception:
                # skip malformed JSON files to avoid crashing the API
                continue
    return items


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.get("/events")
def list_events() -> list[dict]:
    """List stored event JSON payloads."""
    return _read_json_files(EVENTS_DIR)


@app.get("/drafts")
def list_drafts() -> list[dict]:
    """List stored bug draft JSON payloads."""
    return _read_json_files(DRAFTS_DIR)


@app.get("/media/{path:path}")
def get_media(path: str) -> FileResponse:
    """Serve media files from the local ``media`` directory."""
    file_path = (MEDIA_DIR / path).resolve()
    if not str(file_path).startswith(str(MEDIA_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
