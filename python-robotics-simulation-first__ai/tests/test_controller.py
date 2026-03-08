"""Unit tests for the wall-following controller."""

import numpy as np
import pytest

from maze_robot.control.controller import WallFollower, WheelCommand


CONTROLLER = WallFollower(
    desired_wall_dist=0.20,
    front_threshold=0.22,
    base_speed=5.0,
    turn_speed=6.0,
)


def _rays(left: float, front: float, right: float, n: int = 7) -> np.ndarray:
    """Build a simplified ray array: left quarter, centre, right quarter."""
    arr = np.full(n, 1.0)  # default far
    mid = n // 2
    q = max(mid // 2, 1)
    arr[:q] = left
    arr[mid - 1 : mid + 2] = front
    arr[-q:] = right
    return arr


@pytest.mark.parametrize("left,front,right,expect", [
    # Front blocked → should turn right (left > 0, right < 0)
    (0.5, 0.10, 0.5, "turn_right"),
    # Left wall at desired distance, front clear → straight
    (0.20, 0.8, 0.8, "straight"),
    # No left wall (far) → turn left (seek wall)
    (0.90, 0.8, 0.8, "turn_left"),
])
def test_wall_follower_behaviour(left, front, right, expect):
    rays = _rays(left, front, right)
    cmd = CONTROLLER.compute(rays)
    assert isinstance(cmd, WheelCommand)

    if expect == "turn_right":
        assert cmd.left > cmd.right, f"Expected left > right for turn_right, got {cmd}"
    elif expect == "turn_left":
        assert cmd.right > cmd.left, f"Expected right > left for turn_left, got {cmd}"
    elif expect == "straight":
        assert abs(cmd.left - cmd.right) < 3.0, f"Expected ~straight, got {cmd}"


def test_command_types():
    rays = np.full(7, 0.5)
    cmd = CONTROLLER.compute(rays)
    assert isinstance(cmd.left, float)
    assert isinstance(cmd.right, float)
