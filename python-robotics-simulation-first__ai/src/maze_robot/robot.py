"""Differential-drive robot loaded into PyBullet from an inline URDF."""

from __future__ import annotations

import math
import os
import tempfile

import numpy as np
import pybullet as p

# fmt: off
_URDF_TEMPLATE = """\
<?xml version="1.0"?>
<robot name="diff_drive">

  <!-- ==================== CHASSIS ==================== -->
  <link name="chassis">
    <inertial>
      <mass value="1.0"/>
      <origin xyz="0 0 0"/>
      <inertia ixx="0.002" ixy="0" ixz="0" iyy="0.004" iyz="0" izz="0.004"/>
    </inertial>
    <visual>
      <geometry><box size="0.30 0.20 0.05"/></geometry>
      <material name="blue"><color rgba="0.2 0.4 0.8 1"/></material>
    </visual>
    <collision>
      <geometry><box size="0.30 0.20 0.05"/></geometry>
    </collision>
  </link>

  <!-- ==================== LEFT WHEEL ==================== -->
  <link name="left_wheel">
    <inertial>
      <mass value="0.1"/>
      <origin xyz="0 0 0"/>
      <inertia ixx="0.00004" ixy="0" ixz="0" iyy="0.00008" iyz="0" izz="0.00004"/>
    </inertial>
    <visual>
      <geometry><cylinder radius="0.04" length="0.02"/></geometry>
      <material name="black"><color rgba="0.1 0.1 0.1 1"/></material>
    </visual>
    <collision>
      <geometry><cylinder radius="0.04" length="0.02"/></geometry>
    </collision>
  </link>

  <joint name="left_wheel_joint" type="continuous">
    <parent link="chassis"/>
    <child link="left_wheel"/>
    <origin xyz="0.0 0.11 -0.025" rpy="{half_pi} 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <!-- ==================== RIGHT WHEEL ==================== -->
  <link name="right_wheel">
    <inertial>
      <mass value="0.1"/>
      <origin xyz="0 0 0"/>
      <inertia ixx="0.00004" ixy="0" ixz="0" iyy="0.00008" iyz="0" izz="0.00004"/>
    </inertial>
    <visual>
      <geometry><cylinder radius="0.04" length="0.02"/></geometry>
      <material name="black"><color rgba="0.1 0.1 0.1 1"/></material>
    </visual>
    <collision>
      <geometry><cylinder radius="0.04" length="0.02"/></geometry>
    </collision>
  </link>

  <joint name="right_wheel_joint" type="continuous">
    <parent link="chassis"/>
    <child link="right_wheel"/>
    <origin xyz="0.0 -0.11 -0.025" rpy="{half_pi} 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <!-- ==================== CASTER ==================== -->
  <link name="caster">
    <inertial>
      <mass value="0.05"/>
      <origin xyz="0 0 0"/>
      <inertia ixx="0.000004" ixy="0" ixz="0" iyy="0.000004" iyz="0" izz="0.000004"/>
    </inertial>
    <visual>
      <geometry><sphere radius="0.02"/></geometry>
      <material name="grey"><color rgba="0.6 0.6 0.6 1"/></material>
    </visual>
    <collision>
      <geometry><sphere radius="0.02"/></geometry>
    </collision>
  </link>

  <joint name="caster_joint" type="fixed">
    <parent link="chassis"/>
    <child link="caster"/>
    <origin xyz="-0.12 0 -0.045"/>
  </joint>

</robot>
"""
# fmt: on


# Joint name → index mapping (populated after loading)
_LEFT_JOINT = "left_wheel_joint"
_RIGHT_JOINT = "right_wheel_joint"

# Actuation limits
MAX_WHEEL_SPEED = 10.0   # rad/s
MAX_WHEEL_FORCE = 5.0    # N·m

# Physical constants
WHEEL_RADIUS = 0.04      # m
WHEELBASE = 0.22         # m  (center-to-center of wheels, accounting for offsets)


class DiffDriveRobot:
    """A two-wheeled differential-drive robot in PyBullet.

    Spec
    ----
    - Chassis: 0.30 × 0.20 × 0.05 m, 1.0 kg
    - Drive wheels (×2): radius 0.04 m, width 0.02 m, 0.1 kg each
    - Wheelbase: 0.22 m center-to-center
    - Rear caster: sphere radius 0.02 m, 0.05 kg
    - Actuation: velocity-controlled joints, ±10 rad/s, 5 N·m max force
    """

    def __init__(
        self,
        client: int,
        start_pos: tuple[float, float] = (0.0, 0.0),
        start_yaw: float = 0.0,
    ) -> None:
        self._client = client
        self._body_id = self._load_urdf(start_pos, start_yaw)
        self._joint_map = self._build_joint_map()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def body_id(self) -> int:
        return self._body_id

    def set_wheel_velocities(self, left: float, right: float) -> None:
        """Set target angular velocities for left and right wheels (rad/s).

        Clamped to ±MAX_WHEEL_SPEED.
        """
        left = max(-MAX_WHEEL_SPEED, min(MAX_WHEEL_SPEED, left))
        right = max(-MAX_WHEEL_SPEED, min(MAX_WHEEL_SPEED, right))

        p.setJointMotorControl2(
            self._body_id,
            self._joint_map[_LEFT_JOINT],
            p.VELOCITY_CONTROL,
            targetVelocity=left,
            force=MAX_WHEEL_FORCE,
            physicsClientId=self._client,
        )
        p.setJointMotorControl2(
            self._body_id,
            self._joint_map[_RIGHT_JOINT],
            p.VELOCITY_CONTROL,
            targetVelocity=right,
            force=MAX_WHEEL_FORCE,
            physicsClientId=self._client,
        )

    def get_pose(self) -> tuple[float, float, float]:
        """Return (x, y, yaw) of the chassis centre."""
        pos, orn = p.getBasePositionAndOrientation(
            self._body_id, physicsClientId=self._client
        )
        yaw = p.getEulerFromQuaternion(orn)[2]
        return pos[0], pos[1], yaw

    def get_wheel_angles(self) -> tuple[float, float]:
        """Return (left_angle, right_angle) in radians."""
        left = p.getJointState(
            self._body_id, self._joint_map[_LEFT_JOINT],
            physicsClientId=self._client,
        )[0]
        right = p.getJointState(
            self._body_id, self._joint_map[_RIGHT_JOINT],
            physicsClientId=self._client,
        )[0]
        return left, right

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load_urdf(
        self, start_pos: tuple[float, float], start_yaw: float
    ) -> int:
        urdf_str = _URDF_TEMPLATE.format(half_pi=math.pi / 2)
        # PyBullet needs a file path, so write to a temp file.
        fd, path = tempfile.mkstemp(suffix=".urdf")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(urdf_str)
            # Chassis centre sits at wheel-radius + half chassis height
            z = 0.04 + 0.025  # wheel_radius + chassis_half_height
            orn = p.getQuaternionFromEuler([0, 0, start_yaw])
            body_id = p.loadURDF(
                path,
                basePosition=[start_pos[0], start_pos[1], z],
                baseOrientation=orn,
                physicsClientId=self._client,
            )
        finally:
            os.unlink(path)
        return body_id

    def _build_joint_map(self) -> dict[str, int]:
        num = p.getNumJoints(self._body_id, physicsClientId=self._client)
        mapping: dict[str, int] = {}
        for i in range(num):
            info = p.getJointInfo(self._body_id, i, physicsClientId=self._client)
            name = info[1].decode("utf-8")
            mapping[name] = i
        return mapping
