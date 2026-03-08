"""Unit tests for ray-cast distance sensor."""

import math
import numpy as np
import pytest
import pybullet as p
import pybullet_data

from sensors.ray_sensor import RaySensor


@pytest.fixture()
def bullet_client():
    """Spin up a headless PyBullet client with a ground plane."""
    client = p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=client)
    p.setGravity(0, 0, -9.81, physicsClientId=client)
    p.loadURDF("plane.urdf", physicsClientId=client)
    yield client
    p.disconnect(client)


@pytest.fixture()
def robot_at_origin(bullet_client):
    """Place a small box at origin to act as the sensor host."""
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.025],
                                 physicsClientId=bullet_client)
    body = p.createMultiBody(baseMass=1, baseCollisionShapeIndex=col,
                             basePosition=[0, 0, 0.065],
                             physicsClientId=bullet_client)
    return body


def test_empty_world_returns_max_range(bullet_client, robot_at_origin):
    sensor = RaySensor(client=bullet_client, robot_id=robot_at_origin,
                       num_rays=5, max_range=2.0)
    dists = sensor.read()
    assert dists.shape == (5,)
    # No obstacles → every ray should return max_range
    np.testing.assert_allclose(dists, 2.0, atol=0.01)


def test_wall_in_front(bullet_client, robot_at_origin):
    """Place a wall 0.5 m in front; front ray should read ~0.5 m."""
    wall_col = p.createCollisionShape(
        p.GEOM_BOX, halfExtents=[0.01, 1.0, 0.1], physicsClientId=bullet_client
    )
    p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_col,
                      basePosition=[0.5, 0, 0.065], physicsClientId=bullet_client)

    sensor = RaySensor(client=bullet_client, robot_id=robot_at_origin,
                       num_rays=7, max_range=2.0, fov=math.pi)
    dists = sensor.read()
    front = dists[3]  # middle ray
    assert 0.3 < front < 0.6, f"Expected ~0.5m, got {front}"


def test_ray_count_matches(bullet_client, robot_at_origin):
    for n in [1, 3, 7, 12]:
        sensor = RaySensor(client=bullet_client, robot_id=robot_at_origin,
                           num_rays=n, max_range=1.0)
        dists = sensor.read()
        assert dists.shape == (n,)
