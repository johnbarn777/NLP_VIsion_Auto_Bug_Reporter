from __future__ import annotations

from pathlib import Path

from app.detectors.pipeline import DetectorPipeline, NAME_MAP


def test_pipeline_order_respects_yaml(tmp_path: Path):
    cfg = tmp_path / "detectors.yaml"
    # Put flicker first to verify ordering, include all three known
    cfg.write_text("""
detectors:
  - flicker
  - blank
  - freeze
"""
    )

    pipeline = DetectorPipeline.from_yaml(path=cfg)
    names = [type(d).__name__.lower() for d in pipeline.detectors]
    # Lowercased class names end with 'detector'; verify expected order
    assert names[0].startswith("flicker")
    assert names[1].startswith("blank")
    assert names[2].startswith("freeze")


def test_pipeline_unknown_names_are_ignored(tmp_path: Path):
    cfg = tmp_path / "detectors.yaml"
    # Include an unknown detector name; should be skipped
    cfg.write_text("""
detectors:
  - unknown
  - blank
"""
    )

    pipeline = DetectorPipeline.from_yaml(path=cfg)
    names = [type(d).__name__.lower() for d in pipeline.detectors]
    assert len(names) >= 1
    assert names[0].startswith("blank")

