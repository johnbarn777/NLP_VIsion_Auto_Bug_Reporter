"""Dataset utilities and loaders.

Exposes iterators for Atari AAD and Echo+ style datasets that yield
(frames, label) where frames is a list of Paths and label is an
app.schemas.types.AnomalyType.
"""

from .config import get_dataset_root
from .loaders.atari_loader import iterate_atari_clips
from .loaders.echo_loader import iterate_echo_clips

__all__ = [
    "get_dataset_root",
    "iterate_atari_clips",
    "iterate_echo_clips",
]
