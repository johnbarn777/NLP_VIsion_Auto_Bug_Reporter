from __future__ import annotations

from pathlib import Path

from datasets.config import get_dataset_root


def test_get_dataset_root_from_yaml(tmp_path: Path, monkeypatch):
    # Create a temporary YAML config and point the loader to it
    cfg = tmp_path / "config.yaml"
    atari_root = tmp_path / "atari_root"
    echo_root = tmp_path / "echo_root"
    atari_root.mkdir()
    echo_root.mkdir()
    cfg.write_text(
        f"""
atari_aad_root: {atari_root}
echo_plus_root: {echo_root}
"""
    )

    assert get_dataset_root("atari", config_path=cfg) == atari_root.resolve()
    assert get_dataset_root("echo", config_path=cfg) == echo_root.resolve()

