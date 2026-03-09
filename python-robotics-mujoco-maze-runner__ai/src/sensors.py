"""Ray-cast distance sensors using MuJoCo's mj_ray."""

from __future__ import annotations

import math

import mujoco
import numpy as np


class RaySensor:
    """Array of distance-measuring rays fanned across a field of view.

    Rays originate from the robot chassis centre at chassis height and are
    spread evenly across ``fov`` radians.  Each ray returns the distance to
    the first obstacle, or ``max_range`` if nothing is hit.
    """

    def __init__(
        self,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        num_rays: int = 7,
        max_range: float = 1.0,
        fov: float = math.pi,
        ray_height: float = 0.065,
        exclude_body: str = "chassis",
    ) -> None:
        self._model = model
        self._data = data
        self.num_rays = num_rays
        self.max_range = max_range
        self.fov = fov
        self._ray_height = ray_height

        self._exclude_body = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_BODY, exclude_body
        )

        if num_rays == 1:
            self._angles = np.array([0.0])
        else:
            self._angles = np.linspace(-fov / 2, fov / 2, num_rays)

    def read(self) -> np.ndarray:
        """Cast rays and return an array of distances (metres).

        Shape: (num_rays,).  Values are in [0, max_range].
        Index 0 = leftmost ray, index -1 = rightmost ray.
        """
        chassis_id = self._exclude_body
        pos = self._data.xpos[chassis_id].copy()
        rot_mat = self._data.xmat[chassis_id].reshape(3, 3)

        yaw = math.atan2(rot_mat[1, 0], rot_mat[0, 0])

        origin = np.array([pos[0], pos[1], self._ray_height])
        distances = np.empty(self.num_rays)
        geom_id_out = np.array([-1], dtype=np.int32)

        for i, angle_offset in enumerate(self._angles):
            a = yaw + angle_offset
            direction = np.array([math.cos(a), math.sin(a), 0.0])

            dist = mujoco.mj_ray(
                self._model,
                self._data,
                origin,
                direction,
                None,   # geomgroup
                1,      # flg_static: include static geoms
                self._exclude_body,
                geom_id_out,
            )

            if dist < 0 or dist > self.max_range:
                distances[i] = self.max_range
            else:
                distances[i] = dist

        return distances

    @property
    def ray_angles(self) -> np.ndarray:
        """Angular offsets of each ray relative to the robot heading."""
        return self._angles.copy()
