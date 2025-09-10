"""Rolling buffer for recently captured frames."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, List


@dataclass
class FrameRef:
    """Reference to a frame stored on disk."""

    path: Path
    ts: float


class RollingBuffer:
    """Ring buffer keeping roughly N seconds of frame references.

    The buffer stores ``FrameRef`` objects and keeps at most ``fps * seconds``
    entries.  When new frames are appended beyond this capacity, the oldest
    frames are dropped.
    """

    def __init__(self, fps: int, seconds: int) -> None:
        self.fps = fps
        self.seconds = seconds
        self.capacity = fps * seconds
        # ``deque`` drops items automatically when ``maxlen`` is exceeded.
        self._buffer: Deque[FrameRef] = deque(maxlen=self.capacity)

    def append(self, path: Path, ts: float) -> None:
        """Add a new frame reference to the buffer.

        Args:
            path: Path to the stored frame on disk.
            ts: Timestamp when the frame was captured (seconds).
        """

        self._buffer.append(FrameRef(path, ts))

    def to_list(self) -> List[FrameRef]:
        """Return a snapshot list of the buffer contents."""
        return list(self._buffer)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._buffer)
