from __future__ import annotations

import cv2
import numpy as np
from skimage.metrics import structural_similarity


def mad(a: np.ndarray, b: np.ndarray) -> float:
    """Return the mean absolute difference between two images."""
    diff = cv2.absdiff(a, b)
    return float(np.mean(diff))


def ssim(a: np.ndarray, b: np.ndarray) -> float:
    """Return the structural similarity index between two images."""
    a_gray = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY) if a.ndim == 3 else a
    b_gray = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY) if b.ndim == 3 else b
    score, _ = structural_similarity(a_gray, b_gray, full=True)
    return float(score)


__all__ = ["mad", "ssim"]
