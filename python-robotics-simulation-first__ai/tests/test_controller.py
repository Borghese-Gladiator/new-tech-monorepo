"""Unit tests for BeaconFollower controller."""

import math
import pytest
import numpy as np

from sensors.ble_receiver import BLEReading
from control.controller import BeaconFollower, VelocityCommand
from sensors.rssi import rssi_to_distance


def _reading_at_distance(distance: float, tx_power: float = -59.0, n: float = 2.0) -> BLEReading:
    """Helper: build a BLEReading that represents the given distance."""
    rssi = tx_power - 10.0 * n * math.log10(max(distance, 0.01))
    return BLEReading(address="AA:BB:CC:DD:EE:FF", rssi=rssi, tx_power=tx_power)


CONTROLLER = BeaconFollower(kp=0.5, max_speed=1.0, goal_distance=0.3)


@pytest.mark.parametrize("distance,expected_speed_positive,expected_stop", [
    # Far away: robot should move forward (speed > 0)
    (10.0, True, False),
    # Just above goal: small positive speed
    (0.5, True, False),
    # At goal exactly: speed = 0
    (0.3, False, True),
    # Within goal (overshot): speed clamped to 0
    (0.1, False, True),
])
def test_speed_based_on_distance(distance, expected_speed_positive, expected_stop):
    reading = _reading_at_distance(distance)
    cmd = CONTROLLER.compute(reading, robot_position=np.array([0.0, 0.0]), robot_heading=0.0)
    assert isinstance(cmd, VelocityCommand)
    if expected_speed_positive:
        assert cmd.speed > 0, f"Expected speed > 0 at distance={distance}, got {cmd.speed}"
    if expected_stop:
        assert cmd.speed == pytest.approx(0.0, abs=1e-9), (
            f"Expected speed≈0 at distance={distance}, got {cmd.speed}"
        )


def test_speed_capped_at_max():
    reading = _reading_at_distance(100.0)
    cmd = CONTROLLER.compute(reading, robot_position=np.array([0.0, 0.0]), robot_heading=0.0)
    assert cmd.speed <= CONTROLLER.max_speed


@pytest.mark.parametrize("beacon_angle_deg,heading_deg,expected_turn_sign", [
    # Beacon is to the left, robot faces right → should turn left (positive)
    (90.0, 0.0, 1),
    # Beacon is to the right, robot faces left → should turn right (negative)
    (0.0, 90.0, -1),
    # Robot already facing beacon → near-zero turn
    (45.0, 45.0, 0),
])
def test_turn_direction(beacon_angle_deg, heading_deg, expected_turn_sign):
    beacon_rad = math.radians(beacon_angle_deg)
    beacon_pos = np.array([math.cos(beacon_rad) * 5.0, math.sin(beacon_rad) * 5.0])
    robot_pos = np.array([0.0, 0.0])
    heading_rad = math.radians(heading_deg)

    reading = _reading_at_distance(5.0)
    cmd = CONTROLLER.compute(reading, robot_position=robot_pos, robot_heading=heading_rad,
                             beacon_position=beacon_pos)
    if expected_turn_sign == 1:
        assert cmd.turn > 0
    elif expected_turn_sign == -1:
        assert cmd.turn < 0
    else:
        assert abs(cmd.turn) < 1e-6


def test_no_beacon_position_no_turn():
    reading = _reading_at_distance(5.0)
    cmd = CONTROLLER.compute(reading, robot_position=np.array([0.0, 0.0]), robot_heading=0.0)
    assert cmd.turn == 0.0
