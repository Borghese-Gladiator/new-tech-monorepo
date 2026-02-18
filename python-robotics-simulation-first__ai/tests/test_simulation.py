"""Integration test: full simulation loop end-to-end."""

import numpy as np
import pytest
from sim.runner import run_simulation


@pytest.mark.parametrize("beacon,start,steps,tolerance", [
    # Standard case: beacon NE, robot at origin
    (np.array([5.0, 5.0]), np.array([0.0, 0.0]), 200, 0.5),
    # Beacon directly right
    (np.array([10.0, 0.0]), np.array([0.0, 0.0]), 200, 0.5),
    # Short distance
    (np.array([1.0, 1.0]), np.array([0.0, 0.0]), 100, 0.5),
])
def test_robot_reaches_beacon(beacon, start, steps, tolerance):
    robot, world = run_simulation(
        steps=steps, dt=0.1,
        beacon_position=beacon,
        robot_start=start,
        verbose=False,
    )
    dist = world.distance_to_beacon()
    assert dist <= tolerance, (
        f"Robot ended {dist:.3f}m from beacon (tolerance {tolerance}m). "
        f"Final pos: {robot.position}"
    )
