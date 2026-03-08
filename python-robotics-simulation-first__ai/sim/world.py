"""Simulation world: PyBullet physics server, maze, robot, and ground plane."""

from __future__ import annotations

import pybullet as p
import pybullet_data

from sim.maze import Maze
from sim.robot import DiffDriveRobot


class World:
    """Top-level simulation container.

    Creates a PyBullet physics client, spawns a ground plane, generates and
    spawns a maze, and places the differential-drive robot at the start cell.

    Args:
        rows: Maze row count.
        cols: Maze column count.
        cell_size: Side length of each maze cell (metres).
        seed: RNG seed for maze generation.
        gui: If True, open the PyBullet GUI viewer.
    """

    def __init__(
        self,
        rows: int = 5,
        cols: int = 5,
        cell_size: float = 0.5,
        seed: int | None = None,
        gui: bool = False,
    ) -> None:
        mode = p.GUI if gui else p.DIRECT
        self.client = p.connect(mode)

        p.setAdditionalSearchPath(
            pybullet_data.getDataPath(), physicsClientId=self.client
        )
        p.setGravity(0, 0, -9.81, physicsClientId=self.client)

        self._ground_id = p.loadURDF(
            "plane.urdf", physicsClientId=self.client
        )

        # Maze
        self.maze = Maze(rows=rows, cols=cols, cell_size=cell_size)
        self.maze.generate(seed=seed)
        self._wall_ids = self.maze.spawn(self.client)

        # Robot — placed at the centre of cell (0, 0)
        start_x, start_y = self.maze.cell_centre(0, 0)
        self.robot = DiffDriveRobot(
            client=self.client, start_pos=(start_x, start_y), start_yaw=0.0
        )

        # Goal marker (visual only)
        gx, gy = self.maze.goal_position()
        vis = p.createVisualShape(
            p.GEOM_CYLINDER, radius=0.06, length=0.005,
            rgbaColor=[0.1, 0.9, 0.1, 0.8], physicsClientId=self.client,
        )
        self._goal_marker = p.createMultiBody(
            baseMass=0, baseVisualShapeIndex=vis,
            basePosition=[gx, gy, 0.005], physicsClientId=self.client,
        )

        # Camera — point at maze centre, zoom to fit
        if gui:
            mx = cols * cell_size / 2
            my = rows * cell_size / 2
            p.resetDebugVisualizerCamera(
                cameraDistance=max(rows, cols) * cell_size * 0.9,
                cameraYaw=-90,
                cameraPitch=-89,
                cameraTargetPosition=[mx, my, 0],
                physicsClientId=self.client,
            )

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance physics by one fixed timestep (1/240 s by default)."""
        p.stepSimulation(physicsClientId=self.client)

    # ------------------------------------------------------------------
    # Goal check
    # ------------------------------------------------------------------

    def is_at_goal(self, tolerance: float = 0.15) -> bool:
        """True if the robot's (x, y) is within *tolerance* of the goal cell centre."""
        rx, ry, _ = self.robot.get_pose()
        gx, gy = self.maze.goal_position()
        return ((rx - gx) ** 2 + (ry - gy) ** 2) ** 0.5 <= tolerance

    @property
    def goal_position(self) -> tuple[float, float]:
        return self.maze.goal_position()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        p.disconnect(self.client)
