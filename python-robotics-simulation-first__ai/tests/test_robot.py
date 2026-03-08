"""Unit tests for DiffDriveRobot in PyBullet."""

import math
import pytest
import pybullet as p
import pybullet_data

from maze_robot.robot import DiffDriveRobot


@pytest.fixture()
def bullet_client():
    client = p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=client)
    p.setGravity(0, 0, -9.81, physicsClientId=client)
    p.loadURDF("plane.urdf", physicsClientId=client)
    yield client
    p.disconnect(client)


def test_spawn_at_origin(bullet_client):
    robot = DiffDriveRobot(client=bullet_client, start_pos=(0.0, 0.0), start_yaw=0.0)
    x, y, yaw = robot.get_pose()
    assert abs(x) < 0.05
    assert abs(y) < 0.05
    assert abs(yaw) < 0.1


def test_spawn_at_custom_position(bullet_client):
    robot = DiffDriveRobot(client=bullet_client, start_pos=(1.5, 2.0), start_yaw=math.pi / 2)
    x, y, yaw = robot.get_pose()
    assert abs(x - 1.5) < 0.05
    assert abs(y - 2.0) < 0.05
    assert abs(yaw - math.pi / 2) < 0.1


def test_forward_motion(bullet_client):
    """Setting both wheels to positive velocity should move the robot forward (+x)."""
    robot = DiffDriveRobot(client=bullet_client, start_pos=(0.0, 0.0), start_yaw=0.0)
    x0, y0, _ = robot.get_pose()

    robot.set_wheel_velocities(5.0, 5.0)
    for _ in range(500):
        p.stepSimulation(physicsClientId=bullet_client)

    x1, y1, _ = robot.get_pose()
    assert x1 > x0 + 0.05, f"Robot should have moved forward in +x, got x={x1}"


def test_rotation(bullet_client):
    """Opposite wheel velocities should rotate the robot in place."""
    robot = DiffDriveRobot(client=bullet_client, start_pos=(0.0, 0.0), start_yaw=0.0)
    _, _, yaw0 = robot.get_pose()

    # Left forward, right backward → should rotate counter-clockwise (positive yaw)
    robot.set_wheel_velocities(5.0, -5.0)
    for _ in range(500):
        p.stepSimulation(physicsClientId=bullet_client)

    _, _, yaw1 = robot.get_pose()
    # The yaw should have changed significantly
    delta = abs(yaw1 - yaw0)
    assert delta > 0.3, f"Expected significant rotation, got delta_yaw={delta}"
