"""Proportional controller for beacon-following robot."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from sensors.ble_receiver import BLEReading
from sensors.rssi import rssi_to_distance


@dataclass
class WheelCommand:
    """Output of the controller: per-wheel angular velocity targets (rad/s)."""
    left_rad_s: float
    right_rad_s: float


def unicycle_to_wheel(
    v: float,
    omega: float,
    wheel_radius: float,
    wheelbase: float,
) -> WheelCommand:
    """Convert unicycle (v, omega) to differential wheel speeds.

    Args:
        v: Linear velocity (m/s).
        omega: Angular velocity (rad/s, positive = counter-clockwise).
        wheel_radius: Wheel radius in metres.
        wheelbase: Distance between wheel contact points in metres.

    Returns:
        WheelCommand with left_rad_s and right_rad_s.
    """
    left_rad_s = (v - omega * wheelbase / 2.0) / wheel_radius
    right_rad_s = (v + omega * wheelbase / 2.0) / wheel_radius
    return WheelCommand(left_rad_s=left_rad_s, right_rad_s=right_rad_s)


class BeaconFollower:
    """Proportional controller that drives a robot toward a BLE beacon.

    Outputs WheelCommand (rad/s per wheel) via unicycle→differential conversion.

    Args:
        kp: Proportional gain for speed (m/s per metre of error).
        max_speed: Linear speed cap (m/s).
        goal_distance: Target stop distance from beacon (m).
        k_turn: Proportional gain for heading correction (rad/s / rad).
        wheel_radius: Wheel radius passed through to unicycle_to_wheel (m).
        wheelbase: Wheelbase passed through to unicycle_to_wheel (m).
    """

    def __init__(
        self,
        kp: float = 0.5,
        max_speed: float = 1.0,
        goal_distance: float = 0.3,
        k_turn: float = 2.0,
        wheel_radius: float = 0.05,
        wheelbase: float = 0.20,
    ) -> None:
        self.kp = kp
        self.max_speed = max_speed
        self.goal_distance = goal_distance
        self.k_turn = k_turn
        self.wheel_radius = wheel_radius
        self.wheelbase = wheelbase

    def compute(
        self,
        reading: BLEReading,
        robot_position: np.ndarray,
        robot_heading: float,
        beacon_position: np.ndarray | None = None,
    ) -> WheelCommand:
        """Compute wheel velocity targets from a BLE reading.

        Args:
            reading: Latest BLE reading.
            robot_position: Current robot (x, y) in metres.
            robot_heading: Current heading in radians.
            beacon_position: If known, used for bearing-based steering.

        Returns:
            WheelCommand with left_rad_s and right_rad_s.
        """
        distance = rssi_to_distance(reading.rssi, reading.tx_power)
        error = distance - self.goal_distance
        v = max(0.0, min(self.max_speed, self.kp * error))

        omega = 0.0
        if beacon_position is not None:
            delta = np.array(beacon_position, dtype=float) - np.array(robot_position, dtype=float)
            desired_heading = math.atan2(delta[1], delta[0])
            heading_error = _wrap_angle(desired_heading - robot_heading)
            omega = self.k_turn * heading_error

        return unicycle_to_wheel(v, omega, self.wheel_radius, self.wheelbase)


def _wrap_angle(angle: float) -> float:
    """Wrap angle to [-pi, pi]."""
    return (angle + math.pi) % (2 * math.pi) - math.pi
