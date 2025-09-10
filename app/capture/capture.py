"""Screen capture loop writing frames to disk with a rolling buffer."""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np
import yaml

from .buffer import RollingBuffer

try:  # pragma: no cover - optional dependency
    import mss  # type: ignore
except Exception:  # pragma: no cover - executed when mss unavailable
    mss = None


def load_settings() -> Dict:
    """Load capture settings from YAML configuration."""
    cfg_path = Path(__file__).resolve().parent.parent / "config" / "settings.yaml"
    with open(cfg_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def grab(region: Optional[Dict[str, int]] = None) -> np.ndarray:
    """Capture a frame of the screen.

    Tries OpenCV first.  If unavailable, falls back to ``mss``.
    """
    # Attempt OpenCV desktop capture via VideoCapture.  This may not work on all
    # platforms but is attempted first.
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return frame

    if mss is None:
        raise RuntimeError("No screen capture backend available")

    with mss.mss() as sct:
        monitor = region or sct.monitors[1]
        img = sct.grab(monitor)
        return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)


def capture_loop() -> None:
    """Run the capture loop using configured settings."""
    settings = load_settings()
    fps: int = int(settings.get("fps", 5))
    buffer_seconds: int = int(settings.get("buffer_seconds", 5))
    regions = settings.get("regions", {})
    region = regions.get("full") if isinstance(regions, dict) else None

    session = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("data") / "media" / session
    out_dir.mkdir(parents=True, exist_ok=True)

    buffer = RollingBuffer(fps=fps, seconds=buffer_seconds)
    delay = 1.0 / fps

    try:
        while True:
            start = time.time()
            frame = grab(region)
            ts = time.time()
            frame_path = out_dir / f"{ts:.6f}.jpg"
            cv2.imwrite(str(frame_path), frame)
            buffer.append(frame_path, ts)
            sleep_for = delay - (time.time() - start)
            if sleep_for > 0:
                time.sleep(sleep_for)
    except KeyboardInterrupt:  # pragma: no cover - CLI interruption
        pass


def main() -> None:  # pragma: no cover - thin wrapper
    capture_loop()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
