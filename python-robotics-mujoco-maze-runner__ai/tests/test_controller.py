"""Tests for the wall-following controller."""

import numpy as np
import pytest

from src.controller import WallFollower, WheelCommand


@pytest.fixture
def ctrl() -> WallFollower:
    return WallFollower(
        desired_wall_dist=0.20,
        front_threshold=0.22,
        base_speed=5.0,
        turn_speed=6.0,
        wall_kp=15.0,
    )


@pytest.mark.parametrize(
    "rays,expected_behaviour",
    [
        # Front blocked -> turn right (left > 0, right < 0)
        (np.array([1.0, 0.8, 0.5, 0.1, 0.5, 0.8, 1.0]), "turn_right"),
        # No left wall, front clear -> seek left wall
        (np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]), "turn_left"),
        # Left wall at desired distance, front clear -> straight-ish
        (np.array([0.20, 0.25, 0.5, 1.0, 1.0, 1.0, 1.0]), "straight"),
    ],
)
def test_wall_follower_behaviour(
    ctrl: WallFollower, rays: np.ndarray, expected_behaviour: str
) -> None:
    cmd = ctrl.compute(rays)
    if expected_behaviour == "turn_right":
        assert cmd.left > 0
        assert cmd.right < 0
    elif expected_behaviour == "turn_left":
        assert cmd.left < cmd.right
    elif expected_behaviour == "straight":
        # Both wheels positive and roughly similar
        assert cmd.left > 0
        assert cmd.right > 0
