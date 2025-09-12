from __future__ import annotations

from pathlib import Path

from datasets.config import get_dataset_root


def test_env_vars_override_yaml(tmp_path, monkeypatch):
    # YAML points to A, env var to B; env should win
    yaml_cfg = tmp_path / "config.yaml"
    a = tmp_path / "yaml_atari"
    e = tmp_path / "yaml_echo"
    a.mkdir()
    e.mkdir()
    yaml_cfg.write_text(
        f"""
atari_aad_root: {a}
echo_plus_root: {e}
"""
    )

    env_a = tmp_path / "env_atari"
    env_e = tmp_path / "env_echo"
    env_a.mkdir()
    env_e.mkdir()

    monkeypatch.setenv("ATARI_AAD_ROOT", str(env_a))
    monkeypatch.setenv("ECHO_PLUS_ROOT", str(env_e))

    # Even with config_path provided, env should take precedence
    assert get_dataset_root("atari", config_path=yaml_cfg) == env_a.resolve()
    assert get_dataset_root("echo", config_path=yaml_cfg) == env_e.resolve()

