"""Shared helpers: config loading and geometry utilities."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load simulation config from YAML. Falls back to config/sim_config.yaml."""
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config" / "sim_config.yaml"
    else:
        path = Path(path)

    with open(path) as f:
        return yaml.safe_load(f)


def normalize_angle(a: float) -> float:
    """Wrap angle to [-pi, pi]."""
    return math.atan2(math.sin(a), math.cos(a))


def quat_to_yaw(qw: float, qx: float, qy: float, qz: float) -> float:
    """Extract yaw (rotation about z) from a quaternion."""
    siny_cosp = 2 * (qw * qz + qx * qy)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)
