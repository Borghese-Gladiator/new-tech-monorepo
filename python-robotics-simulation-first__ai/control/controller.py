"""Wall-following controller for maze navigation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class WheelCommand:
    """Wheel velocity targets output by the controller (rad/s)."""
    left: float
    right: float


class WallFollower:
    """Left-hand-rule wall follower using ray-cast distance readings.

    Expects an odd number of rays spanning 180° (left → front → right).

    Strategy:
        1. If the front rays detect a wall within ``front_threshold`` → turn right.
        2. If the left-side rays are farther than ``desired_wall_dist`` → turn left
           (seek the wall).
        3. If the left-side rays are closer than ``desired_wall_dist`` → turn right
           (avoid the wall).
        4. Otherwise → drive straight.

    Args:
        desired_wall_dist: Target distance to keep from the left wall (metres).
        front_threshold: Distance at which a frontal obstacle triggers a turn (metres).
        base_speed: Forward wheel speed when driving straight (rad/s).
        turn_speed: Wheel speed differential used for turning (rad/s).
        wall_kp: Proportional gain for lateral wall-distance correction.
    """

    def __init__(
        self,
        desired_wall_dist: float = 0.20,
        front_threshold: float = 0.22,
        base_speed: float = 5.0,
        turn_speed: float = 6.0,
        wall_kp: float = 15.0,
    ) -> None:
        self.desired_wall_dist = desired_wall_dist
        self.front_threshold = front_threshold
        self.base_speed = base_speed
        self.turn_speed = turn_speed
        self.wall_kp = wall_kp

    def compute(self, ray_distances: np.ndarray) -> WheelCommand:
        """Compute wheel command from a ray distance array.

        Args:
            ray_distances: Array of distances, index 0 = leftmost ray,
                           middle = front, last = rightmost.

        Returns:
            WheelCommand with left and right wheel velocities (rad/s).
        """
        n = len(ray_distances)
        mid = n // 2

        # Regions: left quarter, front centre, right quarter
        left_dist = float(np.min(ray_distances[: max(mid // 2, 1)]))
        front_dist = float(np.min(ray_distances[mid - 1 : mid + 2]))
        right_dist = float(np.min(ray_distances[-(max(mid // 2, 1)):]))

        # 1. Front blocked → turn right (in-place or near-in-place)
        if front_dist < self.front_threshold:
            return WheelCommand(left=self.turn_speed, right=-self.turn_speed)

        # 2. No left wall detected (far away) → turn left to find wall
        if left_dist > self.desired_wall_dist * 2.5:
            return WheelCommand(
                left=self.base_speed * 0.3,
                right=self.base_speed,
            )

        # 3. Proportional correction to maintain desired_wall_dist on left
        error = left_dist - self.desired_wall_dist
        correction = self.wall_kp * error

        left_vel = self.base_speed + correction
        right_vel = self.base_speed - correction

        return WheelCommand(left=left_vel, right=right_vel)
