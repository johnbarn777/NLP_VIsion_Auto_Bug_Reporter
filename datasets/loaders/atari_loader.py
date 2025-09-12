from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from app.schemas.types import AnomalyType

LABEL_MAP: Dict[str, AnomalyType] = {
    "blank": AnomalyType.BLANK,
    "freeze": AnomalyType.FREEZE,
    "flicker": AnomalyType.FLICKER,
    "hud_glitch": AnomalyType.HUD_GLITCH,
    # some common variants
    "hud": AnomalyType.HUD_GLITCH,
    "hudglitch": AnomalyType.HUD_GLITCH,
}


def _is_image(p: Path) -> bool:
    return p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}


def _gather_frames(clip_dir: Path) -> List[Path]:
    frames = sorted([p for p in clip_dir.iterdir() if p.is_file() and _is_image(p)])
    return frames


def _iter_label_dirs(
    root: Path, labels: Iterable[str]
) -> Iterator[Tuple[Path, AnomalyType]]:
    for label in labels:
        d = root / label
        if d.exists() and d.is_dir():
            yield d, LABEL_MAP[label]


def iterate_atari_clips(
    root: Optional[Path] = None,
) -> Iterator[Tuple[List[Path], AnomalyType]]:
    """Yield (frames, label) pairs from an Atari AAD-style dataset.

    Expected layout (flexible):
      root/
        blank/clip_xx/{frame.png,...}
        freeze/clip_xx/{frame.png,...}
        flicker/clip_xx/{frame.png,...}
        hud_glitch/clip_xx/{frame.png,...}

    Any directory under a recognized label is treated as a clip directory if it
    contains image files.
    """

    if root is None:
        from datasets.config import get_dataset_root

        r = get_dataset_root("atari")
        if r is None:
            return iter(())  # empty iterator
        root = r

    root = Path(root)
    if not root.exists():
        return iter(())

    labels = [k for k in LABEL_MAP.keys() if (root / k).exists()]
    for label_dir, label in _iter_label_dirs(root, labels):
        for child in sorted(label_dir.iterdir()):
            if child.is_dir():
                frames = _gather_frames(child)
                if frames:
                    yield frames, label
            elif child.is_file() and _is_image(child):
                # single-file clip
                yield [child], label
