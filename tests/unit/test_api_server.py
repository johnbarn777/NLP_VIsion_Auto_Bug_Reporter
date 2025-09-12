from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api import server


def make_sample_dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    events = tmp_path / "events"
    drafts = tmp_path / "drafts"
    media = tmp_path / "media"
    events.mkdir()
    drafts.mkdir()
    media.mkdir()
    return events, drafts, media


def test_health_endpoint():
    client = TestClient(server.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_events_drafts_and_media(tmp_path, monkeypatch):
    events_dir, drafts_dir, media_dir = make_sample_dirs(tmp_path)
    (events_dir / "1.json").write_text('{"id": 1, "type": "blank"}')
    (drafts_dir / "1.json").write_text('{"event_id": 1, "body_md": "# Title"}')
    sample = media_dir / "events" / "1"
    sample.mkdir(parents=True)
    (sample / "screenshot.png").write_bytes(b"img")

    monkeypatch.setattr(server, "EVENTS_DIR", events_dir)
    monkeypatch.setattr(server, "DRAFTS_DIR", drafts_dir)
    monkeypatch.setattr(server, "MEDIA_DIR", media_dir)

    client = TestClient(server.app)
    assert client.get("/events").json() == [{"id": 1, "type": "blank"}]
    assert client.get("/drafts").json() == [{"event_id": 1, "body_md": "# Title"}]
    res = client.get("/media/events/1/screenshot.png")
    assert res.status_code == 200
    assert res.content == b"img"


def test_media_invalid_path(tmp_path, monkeypatch):
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    monkeypatch.setattr(server, "MEDIA_DIR", media_dir)
    from fastapi import HTTPException

    try:
        server.get_media("../secret.txt")
        assert False, "Expected HTTPException for path traversal"
    except HTTPException as exc:
        assert exc.status_code == 400
