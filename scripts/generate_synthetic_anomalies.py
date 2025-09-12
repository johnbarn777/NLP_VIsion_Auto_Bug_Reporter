from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np


@dataclass
class ClipSpec:
    name: str
    label: str
    frames: int
    fps: int
    size: Tuple[int, int]  # (width, height)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_mp4(frames: List[np.ndarray], out_path: Path, fps: int) -> None:
    if not frames:
        raise ValueError("No frames to write")
    h, w, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open writer for {out_path}")
    try:
        for img in frames:
            if img.shape[:2] != (h, w):
                img = cv2.resize(img, (w, h))
            writer.write(img)
    finally:
        writer.release()


def _blank_frames(n: int, size: Tuple[int, int]) -> List[np.ndarray]:
    w, h = size
    return [np.zeros((h, w, 3), dtype=np.uint8) for _ in range(n)]


def _freeze_frames(n: int, size: Tuple[int, int]) -> List[np.ndarray]:
    w, h = size
    base = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    return [base.copy() for _ in range(n)]


def _flicker_frames(n: int, size: Tuple[int, int]) -> List[np.ndarray]:
    w, h = size
    a = np.zeros((h, w, 3), dtype=np.uint8)
    b = np.full((h, w, 3), 255, dtype=np.uint8)
    frames: List[np.ndarray] = []
    for i in range(n):
        frames.append(a if i % 2 == 0 else b)
    return frames


def generate_synthetic_anomalies(out_dir: Path) -> Dict:
    """Generate small labeled MP4s and a ground-truth JSON file.

    Returns the loaded ground truth dictionary.
    """

    _ensure_dir(out_dir)
    size = (128, 128)
    fps = 24
    frames = 60

    specs = [
        ClipSpec(name="blank", label="blank", frames=frames, fps=fps, size=size),
        ClipSpec(name="freeze", label="freeze", frames=frames, fps=fps, size=size),
        ClipSpec(name="flicker", label="flicker", frames=frames, fps=fps, size=size),
    ]

    clips_meta = []
    for spec in specs:
        if spec.label == "blank":
            imgs = _blank_frames(spec.frames, spec.size)
        elif spec.label == "freeze":
            imgs = _freeze_frames(spec.frames, spec.size)
        elif spec.label == "flicker":
            imgs = _flicker_frames(spec.frames, spec.size)
        else:
            raise ValueError(f"Unsupported label {spec.label}")

        out_path = out_dir / f"{spec.name}.mp4"
        _write_mp4(imgs, out_path, spec.fps)
        clips_meta.append(
            {
                "file": str(out_path),
                "label": spec.label,
                "frames": spec.frames,
                "fps": spec.fps,
                "ranges": [
                    {"start_frame": 1, "end_frame": spec.frames, "label": spec.label}
                ],
            }
        )

    truth = {"clips": clips_meta}
    with open(out_dir / "ground_truth.json", "w", encoding="utf-8") as fh:
        json.dump(truth, fh, indent=2)
    return truth


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic anomaly clips")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data") / "synthetic",
        help="Output directory for MP4s and ground truth",
    )
    args = parser.parse_args()
    truth = generate_synthetic_anomalies(args.out)
    print(json.dumps(truth, indent=2))


if __name__ == "__main__":
    main()
