"""Differential drive base: kinematics, actuation, and pose integration."""

from __future__ import annotations

import math
import numpy as np

from sim.robot import Robot


class DriveBase:
    """Two-wheel differential drive base.

    Wraps a Robot and integrates wheel commands into pose updates using
    standard diff-drive forward kinematics each timestep.

    Kinematics (per step):
        v     = wheel_radius * (w_left + w_right) / 2        [m/s linear]
        omega = wheel_radius * (w_right - w_left) / wheelbase [rad/s angular]
        dx    = v * cos(heading) * dt
        dy    = v * sin(heading) * dt
        dtheta = omega * dt

    Args:
        robot: The Robot instance whose pose this DriveBase owns.
        wheel_radius: Radius of each wheel in metres.
        wheelbase: Distance between left and right contact points in metres.
        max_wheel_speed: Maximum |angular velocity| per wheel in rad/s.
        max_wheel_accel: Optional acceleration limit in rad/s^2.
                         None means instantaneous (no ramp).
    """

    def __init__(
        self,
        robot: Robot,
        wheel_radius: float = 0.05,
        wheelbase: float = 0.20,
        max_wheel_speed: float = 20.0,
        max_wheel_accel: float | None = None,
    ) -> None:
        if wheel_radius <= 0:
            raise ValueError(f"wheel_radius must be positive, got {wheel_radius}")
        if wheelbase <= 0:
            raise ValueError(f"wheelbase must be positive, got {wheelbase}")
        if max_wheel_speed <= 0:
            raise ValueError(f"max_wheel_speed must be positive, got {max_wheel_speed}")

        self.robot = robot
        self.wheel_radius = wheel_radius
        self.wheelbase = wheelbase
        self.max_wheel_speed = max_wheel_speed
        self.max_wheel_accel = max_wheel_accel

        # Current actual wheel speeds (rad/s)
        self._left_speed: float = 0.0
        self._right_speed: float = 0.0

        # Targets set by set_wheel_targets()
        self._left_target: float = 0.0
        self._right_target: float = 0.0

        # Cumulative wheel angles (rad) — used by encoders
        self.left_angle: float = 0.0
        self.right_angle: float = 0.0

    def set_wheel_targets(self, left_rad_s: float, right_rad_s: float) -> None:
        """Set desired wheel angular velocities (rad/s).

        Values are clamped to [-max_wheel_speed, +max_wheel_speed].
        """
        clamp = self.max_wheel_speed
        self._left_target = max(-clamp, min(clamp, left_rad_s))
        self._right_target = max(-clamp, min(clamp, right_rad_s))

    def step(self, dt: float) -> None:
        """Advance the drive base by one timestep.

        Applies optional acceleration limits, integrates wheel angles,
        then updates the robot pose via diff-drive kinematics.
        """
        self._left_speed = self._apply_accel(self._left_speed, self._left_target, dt)
        self._right_speed = self._apply_accel(self._right_speed, self._right_target, dt)

        # Integrate wheel angles
        self.left_angle += self._left_speed * dt
        self.right_angle += self._right_speed * dt

        # Diff-drive forward kinematics
        v = self.wheel_radius * (self._left_speed + self._right_speed) / 2.0
        omega = self.wheel_radius * (self._right_speed - self._left_speed) / self.wheelbase

        self.robot.position[0] += math.cos(self.robot.heading) * v * dt
        self.robot.position[1] += math.sin(self.robot.heading) * v * dt
        self.robot.heading = (self.robot.heading + omega * dt) % (2 * math.pi)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_accel(self, current: float, target: float, dt: float) -> float:
        """Ramp current toward target, respecting max_wheel_accel if set."""
        if self.max_wheel_accel is None:
            return target
        delta = target - current
        max_delta = self.max_wheel_accel * dt
        return current + max(-max_delta, min(max_delta, delta))
