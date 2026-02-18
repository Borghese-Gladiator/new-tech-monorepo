"""Proportional controller for beacon-following robot."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from sensors.ble_receiver import BLEReading
from sensors.rssi import rssi_to_distance


@dataclass
class VelocityCommand:
    """Output of the controller: linear speed and heading correction."""
    speed: float    # m/s forward
    turn: float     # rad, positive = counter-clockwise


class BeaconFollower:
    """Proportional controller that drives a robot toward a BLE beacon.

    The controller uses:
    - Distance (from RSSI) for forward speed: v = kp * (distance - goal).
    - An optional bearing vector (robot→beacon) for heading correction.

    Args:
        kp: Proportional gain for speed (m/s per metre of error).
        max_speed: Speed cap (m/s).
        goal_distance: Target distance from beacon to stop (m).
        k_turn: Proportional gain for heading correction (rad/rad).
    """

    def __init__(
        self,
        kp: float = 0.5,
        max_speed: float = 1.0,
        goal_distance: float = 0.3,
        k_turn: float = 2.0,
    ) -> None:
        self.kp = kp
        self.max_speed = max_speed
        self.goal_distance = goal_distance
        self.k_turn = k_turn

    def compute(
        self,
        reading: BLEReading,
        robot_position: np.ndarray,
        robot_heading: float,
        beacon_position: np.ndarray | None = None,
    ) -> VelocityCommand:
        """Compute a velocity command from a BLE reading.

        Args:
            reading: Latest BLE reading.
            robot_position: Current robot (x, y) in metres.
            robot_heading: Current heading in radians.
            beacon_position: If known, used for bearing-based steering.
                             If None, the robot just drives straight.

        Returns:
            VelocityCommand with speed and turn.
        """
        distance = rssi_to_distance(reading.rssi, reading.tx_power)
        error = distance - self.goal_distance
        speed = max(0.0, min(self.max_speed, self.kp * error))

        turn = 0.0
        if beacon_position is not None:
            delta = np.array(beacon_position, dtype=float) - np.array(robot_position, dtype=float)
            desired_heading = math.atan2(delta[1], delta[0])
            heading_error = _wrap_angle(desired_heading - robot_heading)
            turn = self.k_turn * heading_error

        return VelocityCommand(speed=speed, turn=turn)


def _wrap_angle(angle: float) -> float:
    """Wrap angle to [-pi, pi]."""
    return (angle + math.pi) % (2 * math.pi) - math.pi
