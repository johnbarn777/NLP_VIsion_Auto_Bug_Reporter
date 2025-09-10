import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.detectors.blank import detect


def test_blank_detector_false():
    assert detect(None) is False
