from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from app.schemas.types import AnomalyType

# Echo+ assumed to use similar label names; allow variants
LABEL_MAP: Dict[str, AnomalyType] = {
    "blank": AnomalyType.BLANK,
    "freeze": AnomalyType.FREEZE,
    "flicker": AnomalyType.FLICKER,
    "hud_glitch": AnomalyType.HUD_GLITCH,
    "hud": AnomalyType.HUD_GLITCH,
    "hudglitch": AnomalyType.HUD_GLITCH,
}


def _is_image(p: Path) -> bool:
    return p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}


def _gather_frames(clip_dir: Path) -> List[Path]:
    frames = sorted([p for p in clip_dir.iterdir() if p.is_file() and _is_image(p)])
    return frames


def iterate_echo_clips(root: Optional[Path] = None) -> Iterator[Tuple[List[Path], AnomalyType]]:
    """Yield (frames, label) pairs from an Echo+-style dataset.

    Accepts a layout similar to Atari AAD, but we do not assume a strict
    directory depth. Any subdirectory directly under the dataset root whose
    name matches a known label is treated as the label folder.
    """

    if root is None:
        from datasets.config import get_dataset_root

        r = get_dataset_root("echo")
        if r is None:
            return iter(())
        root = r

    root = Path(root)
    if not root.exists():
        return iter(())

    for label_name, label in LABEL_MAP.items():
        label_dir = root / label_name
        if not label_dir.exists() or not label_dir.is_dir():
            continue
        # A clip is either a directory with frames or a single image file
        for child in sorted(label_dir.iterdir()):
            if child.is_dir():
                frames = _gather_frames(child)
                if frames:
                    yield frames, label
            elif child.is_file() and _is_image(child):
                yield [child], label


