"""2-D robot model."""

import math
import numpy as np


class Robot:
    """A point robot on a 2-D plane.

    Attributes:
        position: (x, y) in metres.
        heading: Direction the robot faces, in radians (0 = +x axis).
    """

    def __init__(self, position: np.ndarray, heading: float = 0.0) -> None:
        self.position = np.array(position, dtype=float)
        self.heading = float(heading)

    def move(self, speed: float, dt: float) -> None:
        """Advance the robot forward by speed * dt metres along its heading."""
        self.position[0] += math.cos(self.heading) * speed * dt
        self.position[1] += math.sin(self.heading) * speed * dt

    def turn(self, angle: float) -> None:
        """Rotate the robot by angle radians (positive = counter-clockwise)."""
        self.heading = (self.heading + angle) % (2 * math.pi)

    def __repr__(self) -> str:
        deg = math.degrees(self.heading)
        return f"Robot(pos={self.position}, heading={deg:.1f}°)"
