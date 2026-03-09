"""Differential-drive robot: MJCF generation and runtime interface."""

from __future__ import annotations

from dataclasses import dataclass

import mujoco

from src.utils import quat_to_yaw


@dataclass
class RobotSpec:
    """Physical dimensions and limits for the differential-drive robot."""
    wheel_radius: float = 0.04
    wheelbase: float = 0.22
    chassis_half_size: tuple[float, float, float] = (0.15, 0.10, 0.025)
    max_wheel_speed: float = 10.0
    actuator_kv: float = 0.5

    @property
    def chassis_z(self) -> float:
        """Height of chassis centre above ground (wheel_radius + chassis_half_height)."""
        return self.wheel_radius + self.chassis_half_size[2]


def robot_mjcf(spec: RobotSpec | None = None) -> str:
    """Return the MJCF XML fragment for the differential-drive robot body."""
    if spec is None:
        spec = RobotSpec()

    cz = spec.chassis_z
    chx, chy, chz = spec.chassis_half_size
    wr = spec.wheel_radius
    wb_half = spec.wheelbase / 2

    return f"""\
    <body name="chassis" pos="0 0 {cz}">
      <freejoint name="chassis_free"/>
      <inertial pos="0 0 0" mass="1.0"
                diaginertia="0.004 0.002 0.004"/>
      <geom name="chassis_geom" type="box" size="{chx} {chy} {chz}"
            rgba="0.2 0.4 0.8 1"/>

      <!-- Left wheel -->
      <body name="left_wheel" pos="0.0 {wb_half} {-chz}">
        <joint name="left_wheel_joint" type="hinge" axis="0 1 0"
               damping="0.001"/>
        <inertial pos="0 0 0" mass="0.1"
                  diaginertia="0.00008 0.00004 0.00004"/>
        <geom name="left_wheel_geom" type="cylinder" size="{wr} 0.01"
              euler="90 0 0"
              rgba="0.1 0.1 0.1 1" condim="4"
              friction="1.5 0.005 0.001" priority="1"/>
      </body>

      <!-- Right wheel -->
      <body name="right_wheel" pos="0.0 {-wb_half} {-chz}">
        <joint name="right_wheel_joint" type="hinge" axis="0 1 0"
               damping="0.001"/>
        <inertial pos="0 0 0" mass="0.1"
                  diaginertia="0.00008 0.00004 0.00004"/>
        <geom name="right_wheel_geom" type="cylinder" size="{wr} 0.01"
              euler="90 0 0"
              rgba="0.1 0.1 0.1 1" condim="4"
              friction="1.5 0.005 0.001" priority="1"/>
      </body>

      <!-- Caster (fixed) -->
      <body name="caster" pos="-0.12 0 {-(cz - 0.02)}">
        <inertial pos="0 0 0" mass="0.05"
                  diaginertia="0.000004 0.000004 0.000004"/>
        <geom name="caster_geom" type="sphere" size="0.02"
              rgba="0.6 0.6 0.6 1" condim="1"
              friction="0.01 0.001 0.001"/>
      </body>
    </body>
"""


def robot_actuators_mjcf(spec: RobotSpec | None = None) -> str:
    """Return MJCF actuator elements for the two wheel joints."""
    if spec is None:
        spec = RobotSpec()

    mws = spec.max_wheel_speed
    kv = spec.actuator_kv

    return f"""\
    <velocity name="left_wheel_vel" joint="left_wheel_joint"
              kv="{kv}" ctrlrange="{-mws} {mws}"/>
    <velocity name="right_wheel_vel" joint="right_wheel_joint"
              kv="{kv}" ctrlrange="{-mws} {mws}"/>
"""


class DiffDriveRobot:
    """Runtime interface for the two-wheeled differential-drive robot."""

    def __init__(
        self, model: mujoco.MjModel, data: mujoco.MjData, max_wheel_speed: float = 10.0
    ) -> None:
        self._model = model
        self._data = data
        self._max_wheel_speed = max_wheel_speed

        self._left_act = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "left_wheel_vel")
        self._right_act = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "right_wheel_vel")
        self._chassis_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "chassis")

    def set_wheel_velocities(self, left: float, right: float) -> None:
        """Set target angular velocities for left and right wheels (rad/s)."""
        mws = self._max_wheel_speed
        left = max(-mws, min(mws, left))
        right = max(-mws, min(mws, right))
        self._data.ctrl[self._left_act] = left
        self._data.ctrl[self._right_act] = right

    def get_pose(self) -> tuple[float, float, float]:
        """Return (x, y, yaw) of the chassis centre."""
        qpos_adr = self._model.jnt_qposadr[
            mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_JOINT, "chassis_free")
        ]
        x = float(self._data.qpos[qpos_adr])
        y = float(self._data.qpos[qpos_adr + 1])
        qw = self._data.qpos[qpos_adr + 3]
        qx = self._data.qpos[qpos_adr + 4]
        qy = self._data.qpos[qpos_adr + 5]
        qz = self._data.qpos[qpos_adr + 6]
        yaw = quat_to_yaw(qw, qx, qy, qz)
        return x, y, float(yaw)
