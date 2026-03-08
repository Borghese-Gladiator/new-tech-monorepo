"""Ray-cast distance sensors using PyBullet's rayTestBatch."""

from __future__ import annotations

import math

import numpy as np
import pybullet as p


class RaySensor:
    """Array of distance-measuring rays fanned across a field of view.

    Rays originate from the robot chassis centre at chassis height and are
    spread evenly across ``fov`` radians.  Each ray returns the distance to
    the first obstacle, or ``max_range`` if nothing is hit.

    Args:
        client: PyBullet physics client ID.
        robot_id: Body ID of the robot (used for pose lookup).
        num_rays: Number of rays.
        max_range: Maximum sensing distance (metres).
        fov: Total field of view (radians). Default π (180°).
        ray_height: Height offset above ground for ray origin (metres).
    """

    def __init__(
        self,
        client: int,
        robot_id: int,
        num_rays: int = 7,
        max_range: float = 1.0,
        fov: float = math.pi,
        ray_height: float = 0.065,
    ) -> None:
        self._client = client
        self._robot_id = robot_id
        self.num_rays = num_rays
        self.max_range = max_range
        self.fov = fov
        self._ray_height = ray_height

        # Pre-compute angular offsets relative to robot heading
        if num_rays == 1:
            self._angles = np.array([0.0])
        else:
            self._angles = np.linspace(-fov / 2, fov / 2, num_rays)

    def read(self) -> np.ndarray:
        """Cast rays and return an array of distances (metres).

        Shape: (num_rays,).  Values are in [0, max_range].
        Index 0 = leftmost ray, index -1 = rightmost ray.
        """
        pos, orn = p.getBasePositionAndOrientation(
            self._robot_id, physicsClientId=self._client
        )
        yaw = p.getEulerFromQuaternion(orn)[2]

        origin = [pos[0], pos[1], self._ray_height]
        ray_froms = []
        ray_tos = []

        for angle_offset in self._angles:
            a = yaw + angle_offset
            dx = math.cos(a) * self.max_range
            dy = math.sin(a) * self.max_range
            ray_froms.append(origin)
            ray_tos.append([origin[0] + dx, origin[1] + dy, self._ray_height])

        results = p.rayTestBatch(
            ray_froms, ray_tos, physicsClientId=self._client
        )

        distances = np.empty(self.num_rays)
        for i, res in enumerate(results):
            hit_fraction = res[2]  # 1.0 means no hit
            distances[i] = hit_fraction * self.max_range

        return distances

    @property
    def ray_angles(self) -> np.ndarray:
        """Angular offsets of each ray relative to the robot heading (radians)."""
        return self._angles.copy()
