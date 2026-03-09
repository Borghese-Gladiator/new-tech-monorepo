"""Wall-following controller for maze navigation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import numpy as np


@dataclass
class WheelCommand:
    """Wheel velocity targets output by the controller (rad/s)."""
    left: float
    right: float


class _State(Enum):
    FOLLOW_WALL = auto()
    TURN_RIGHT = auto()


class WallFollower:
    """Left-hand-rule wall follower using ray-cast distance readings.

    Expects an odd number of rays spanning 180 deg (left -> front -> right).

    Uses a simple state machine to avoid oscillation:
        FOLLOW_WALL: drive forward, maintaining left wall distance.
        TURN_RIGHT: rotate right in-place until front is sufficiently clear.
    """

    def __init__(
        self,
        desired_wall_dist: float = 0.20,
        front_threshold: float = 0.25,
        clear_threshold: float = 0.35,
        base_speed: float = 3.0,
        turn_speed: float = 4.0,
        wall_kp: float = 10.0,
    ) -> None:
        self.desired_wall_dist = desired_wall_dist
        self.front_threshold = front_threshold
        self.clear_threshold = clear_threshold
        self.base_speed = base_speed
        self.turn_speed = turn_speed
        self.wall_kp = wall_kp
        self._state = _State.FOLLOW_WALL

    def compute(self, ray_distances: np.ndarray) -> WheelCommand:
        """Compute wheel command from a ray distance array.

        Index 0 = leftmost ray, middle = front, last = rightmost.
        """
        n = len(ray_distances)
        mid = n // 2

        left_dist = float(np.min(ray_distances[: max(mid // 2, 1)]))
        front_dist = float(np.min(ray_distances[mid - 1 : mid + 2]))

        # State transitions
        if self._state == _State.FOLLOW_WALL and front_dist < self.front_threshold:
            self._state = _State.TURN_RIGHT
        elif self._state == _State.TURN_RIGHT and front_dist > self.clear_threshold:
            self._state = _State.FOLLOW_WALL

        # Actions
        if self._state == _State.TURN_RIGHT:
            return WheelCommand(left=self.turn_speed, right=-self.turn_speed)

        # FOLLOW_WALL state
        # No left wall -> turn left to seek wall
        if left_dist > self.desired_wall_dist * 2.5:
            return WheelCommand(
                left=self.base_speed * 0.3,
                right=self.base_speed,
            )

        # Proportional correction to maintain left wall distance
        error = left_dist - self.desired_wall_dist
        correction = self.wall_kp * error

        left_vel = self.base_speed + correction
        right_vel = self.base_speed - correction

        return WheelCommand(left=left_vel, right=right_vel)
