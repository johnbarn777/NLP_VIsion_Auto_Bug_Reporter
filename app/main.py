"""Entry point wiring capture, detection and storage via asyncio queues."""

from __future__ import annotations

import asyncio
from asyncio import Queue

from app.detectors.pipeline import DetectorPipeline
from app.schemas.models import AnomalyEvent, FramePacket
from app.storage import artifacts, repo
from app.storage.db import session_scope


async def capture_loop(frame_q: Queue[FramePacket]) -> None:
    """Placeholder for frame capture logic.

    This mock loop currently does nothing but is structured to put
    :class:`FramePacket` objects onto ``frame_q`` in a real implementation.
    """

    while True:  # pragma: no cover - loop body is placeholder
        await asyncio.sleep(1)


async def detect_loop(
    frame_q: Queue[FramePacket], event_q: Queue[AnomalyEvent]
) -> None:
    """Consume frames, run detectors and emit events."""

    pipeline = DetectorPipeline.from_yaml()
    while True:
        pkt = await frame_q.get()
        events = pipeline.process(pkt)
        for evt in events:
            await event_q.put(evt)


async def event_loop(event_q: Queue[AnomalyEvent]) -> None:
    """Persist events and associated artifacts."""

    with session_scope() as session:
        while True:
            evt = await event_q.get()
            repo.save_event(session, evt)
            artifacts.save_event_artifacts(evt)


async def main() -> None:
    """Run capture, detection and storage concurrently."""

    frame_q: Queue[FramePacket] = asyncio.Queue()
    event_q: Queue[AnomalyEvent] = asyncio.Queue()
    await asyncio.gather(
        capture_loop(frame_q),
        detect_loop(frame_q, event_q),
        event_loop(event_q),
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry
    asyncio.run(main())
