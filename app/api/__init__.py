"""Minimal FastAPI application for health checks."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint used for container liveness."""
    return {"status": "ok"}


__all__ = ["app"]
