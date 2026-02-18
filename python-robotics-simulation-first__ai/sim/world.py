"""Simulation world: holds the beacon position and the robot."""

import numpy as np
from sim.robot import Robot


class World:
    """A 2-D simulation environment.

    Attributes:
        beacon_position: Fixed (x, y) position of the BLE beacon.
        robot: The robot instance being simulated.
    """

    def __init__(self, beacon_position: np.ndarray, robot: Robot) -> None:
        self.beacon_position = np.array(beacon_position, dtype=float)
        self.robot = robot

    def distance_to_beacon(self) -> float:
        """Euclidean distance from the robot to the beacon (metres)."""
        return float(np.linalg.norm(self.robot.position - self.beacon_position))
