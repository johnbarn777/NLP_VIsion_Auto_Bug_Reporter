from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class ClipSettings:
    """Configure pre/post windows for saved clips."""

    pre: int = 2
    post: int = 2


@dataclass
class BlankConfig:
    luma_thresh: int = 10
    sat_thresh: int = 15
    pct: float = 0.95
    frames: int = 3


@dataclass
class FreezeConfig:
    mad: float = 1.0
    frames: int = 3


@dataclass
class FlickerConfig:
    window: int = 8
    ratio_thresh: float = 0.6


@dataclass
class DetectorConfigs:
    blank: BlankConfig = field(default_factory=BlankConfig)
    freeze: FreezeConfig = field(default_factory=FreezeConfig)
    flicker: FlickerConfig = field(default_factory=FlickerConfig)


@dataclass
class Settings:
    fps: int = 5
    buffer_seconds: int = 5
    clip: ClipSettings = field(default_factory=ClipSettings)
    detectors: DetectorConfigs = field(default_factory=DetectorConfigs)
    regions: Dict[str, Dict[str, int]] = field(default_factory=dict)


_DEFAULT_PATH = Path(__file__).resolve().with_name("settings.yaml")


def _parse_env(val: str) -> Any:
    """Best-effort parse of environment variables into native types."""
    if val.lower() in {"true", "false"}:
        return val.lower() == "true"
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def _apply_env_overrides(cfg: Dict[str, Any]) -> None:
    detectors = cfg.setdefault("detectors", {})
    clip = cfg.setdefault("clip", {})
    for env_key, env_val in os.environ.items():
        key = env_key.lower()
        parts = key.split("_")
        if key == "fps":
            cfg["fps"] = _parse_env(env_val)
        elif key == "buffer_seconds":
            cfg["buffer_seconds"] = _parse_env(env_val)
        elif parts[0] == "clip" and len(parts) > 1:
            clip[parts[1]] = _parse_env(env_val)
        elif parts[0] in {"blank", "freeze", "flicker"} and len(parts) > 1:
            det = detectors.setdefault(parts[0], {})
            det[parts[1]] = _parse_env(env_val)


def load_settings(path: Path | None = None) -> Settings:
    """Load settings from YAML, applying environment overrides."""
    path = path or _DEFAULT_PATH
    data: Dict[str, Any]
    if path.exists():
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    else:
        data = {}

    _apply_env_overrides(data)

    clip_cfg = data.get("clip", {})
    det_cfg = data.get("detectors", {})

    settings = Settings(
        fps=int(data.get("fps", 5)),
        buffer_seconds=int(data.get("buffer_seconds", 5)),
        clip=ClipSettings(
            pre=int(clip_cfg.get("pre", 2)),
            post=int(clip_cfg.get("post", 2)),
        ),
        detectors=DetectorConfigs(
            blank=BlankConfig(
                luma_thresh=int(det_cfg.get("blank", {}).get("luma_thresh", 10)),
                sat_thresh=int(det_cfg.get("blank", {}).get("sat_thresh", 15)),
                pct=float(det_cfg.get("blank", {}).get("pct", 0.95)),
                frames=int(det_cfg.get("blank", {}).get("frames", 3)),
            ),
            freeze=FreezeConfig(
                mad=float(det_cfg.get("freeze", {}).get("mad", 1.0)),
                frames=int(det_cfg.get("freeze", {}).get("frames", 3)),
            ),
            flicker=FlickerConfig(
                window=int(det_cfg.get("flicker", {}).get("window", 8)),
                ratio_thresh=float(det_cfg.get("flicker", {}).get("ratio_thresh", 0.6)),
            ),
        ),
        regions=data.get("regions", {}),
    )

    return settings


__all__ = ["Settings", "load_settings"]
