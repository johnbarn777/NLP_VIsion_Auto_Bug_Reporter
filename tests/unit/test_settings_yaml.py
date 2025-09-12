from __future__ import annotations

from pathlib import Path

from app.config.load import load_settings


def test_load_settings_from_yaml(tmp_path: Path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
fps: 12
buffer_seconds: 7
clip:
  pre: 3
  post: 4
detectors:
  blank:
    luma_thresh: 20
    sat_thresh: 25
    pct: 0.9
    frames: 5
  freeze:
    mad: 2.5
    frames: 6
  flicker:
    window: 10
    ratio_thresh: 0.7
"""
    )

    st = load_settings(path=cfg)
    assert st.fps == 12
    assert st.buffer_seconds == 7
    assert st.clip.pre == 3 and st.clip.post == 4
    assert st.detectors.blank.luma_thresh == 20
    assert st.detectors.blank.sat_thresh == 25
    assert abs(st.detectors.blank.pct - 0.9) < 1e-9
    assert st.detectors.blank.frames == 5
    assert abs(st.detectors.freeze.mad - 2.5) < 1e-9
    assert st.detectors.freeze.frames == 6
    assert st.detectors.flicker.window == 10
    assert abs(st.detectors.flicker.ratio_thresh - 0.7) < 1e-9

