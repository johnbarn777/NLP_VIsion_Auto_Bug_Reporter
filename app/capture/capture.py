"""Screen capture loop writing frames to disk with a rolling buffer."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import yaml

from .buffer import RollingBuffer

try:  # pragma: no cover - optional dependency
    import cv2  # type: ignore
except Exception:  # pragma: no cover - executed when OpenCV unavailable
    cv2 = None

try:  # pragma: no cover - optional dependency
    import mss  # type: ignore
except Exception:  # pragma: no cover - executed when mss unavailable
    mss = None

try:  # pragma: no cover - optional dependency
    from PIL import Image
except Exception:  # pragma: no cover - executed when Pillow unavailable
    Image = None


def load_settings() -> Dict:
    """Load capture settings from YAML configuration."""
    cfg_path = Path(__file__).resolve().parent.parent / "config" / "settings.yaml"
    with open(cfg_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def grab(region: Optional[Dict[str, int]] = None) -> np.ndarray:
    """Capture a frame of the screen.

    Uses ``mss`` for screen capture and optionally converts color space with
    OpenCV if available.
    """
    if mss is None:
        raise RuntimeError("No screen capture backend available")

    with mss.mss() as sct:
        monitor = region or sct.monitors[1]
        img = sct.grab(monitor)
        frame = np.array(img)
        if cv2 is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        else:  # drop alpha channel if OpenCV not present
            frame = frame[:, :, :3]
        return frame


def save_frame(frame: np.ndarray, path: Path) -> None:
    """Write a frame to disk as JPEG."""
    if cv2 is not None:
        cv2.imwrite(str(path), frame)
    elif Image is not None:
        Image.fromarray(frame).save(path, format="JPEG")
    else:  # pragma: no cover - executed only if no writer available
        raise RuntimeError("No image writer available")


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
            save_frame(frame, frame_path)
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
