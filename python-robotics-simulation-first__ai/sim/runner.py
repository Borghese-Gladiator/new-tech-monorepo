"""Simulation runner: ticks the world, reads BLE, runs controller, moves robot."""

from __future__ import annotations

import numpy as np

from sim.robot import Robot
from sim.world import World
from sensors.simulated_ble import SimulatedBLEReceiver
from control.controller import BeaconFollower


def run_simulation(
    steps: int = 100,
    dt: float = 0.1,
    beacon_position: np.ndarray | None = None,
    robot_start: np.ndarray | None = None,
    verbose: bool = True,
) -> tuple[Robot, World]:
    """Run the beacon-following simulation.

    Args:
        steps: Number of simulation steps.
        dt: Time step in seconds.
        beacon_position: (x, y) of the BLE beacon. Defaults to (5, 5).
        robot_start: (x, y) starting position. Defaults to (0, 0).
        verbose: Print position each step.

    Returns:
        (robot, world) after the simulation finishes.
    """
    if beacon_position is None:
        beacon_position = np.array([5.0, 5.0])
    if robot_start is None:
        robot_start = np.array([0.0, 0.0])

    robot = Robot(position=robot_start)
    world = World(beacon_position=beacon_position, robot=robot)

    ble = SimulatedBLEReceiver(
        beacon_position=beacon_position,
        robot_position_fn=lambda: robot.position.copy(),
        noise_std=0.5,
        rng=np.random.default_rng(42),
    )
    controller = BeaconFollower(kp=0.8, max_speed=1.5, goal_distance=0.3)

    for step in range(steps):
        reading = ble.read()
        cmd = controller.compute(
            reading,
            robot_position=robot.position,
            robot_heading=robot.heading,
            beacon_position=beacon_position,
        )
        robot.turn(cmd.turn * dt)
        robot.move(cmd.speed, dt)

        dist = world.distance_to_beacon()
        if verbose:
            print(
                f"step {step:3d} | pos=({robot.position[0]:6.2f}, {robot.position[1]:6.2f})"
                f" | dist={dist:.2f}m | speed={cmd.speed:.2f} | turn={cmd.turn:.2f}"
            )
        if dist <= controller.goal_distance:
            if verbose:
                print(f"  -> Reached beacon at step {step}!")
            break

    return robot, world


if __name__ == "__main__":
    robot, world = run_simulation(steps=200, dt=0.1, verbose=True)
    print(f"\nFinal distance to beacon: {world.distance_to_beacon():.3f} m")
