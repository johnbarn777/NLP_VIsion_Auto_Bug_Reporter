from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml


_DEFAULT_CONFIG_PATH = Path("datasets") / "config.yaml"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        return {}
    return data


def get_dataset_root(
    name: str, *, config_path: Optional[Path] = None
) -> Optional[Path]:
    """Return dataset root for a given dataset name.

    Precedence:
    - Environment variables (ATARI_AAD_ROOT, ECHO_PLUS_ROOT)
    - YAML file at datasets/config.yaml with keys atari_aad_root, echo_plus_root
    - None if not configured
    """

    env_map = {
        "atari": "ATARI_AAD_ROOT",
        "echo": "ECHO_PLUS_ROOT",
        "atari_aad": "ATARI_AAD_ROOT",
        "echo_plus": "ECHO_PLUS_ROOT",
    }

    yaml_map = {
        "atari": "atari_aad_root",
        "echo": "echo_plus_root",
        "atari_aad": "atari_aad_root",
        "echo_plus": "echo_plus_root",
    }

    # Environment variable
    env_key = env_map.get(name.lower())
    if env_key:
        env_val = os.environ.get(env_key)
        if env_val:
            p = Path(env_val).expanduser().resolve()
            return p

    # YAML file
    cfg_path = config_path or _DEFAULT_CONFIG_PATH
    cfg = _load_yaml(cfg_path)
    y_key = yaml_map.get(name.lower())
    if y_key and isinstance(cfg.get(y_key), (str, Path)):
        return Path(cfg[y_key]).expanduser().resolve()

    return None
