"""Simulation runner: sense → decide → act → step loop."""

from __future__ import annotations

import time as _time

from sim.world import World
from maze_robot.sensors.ray_sensor import RaySensor
from maze_robot.control.controller import WallFollower


def run_simulation(
    rows: int = 5,
    cols: int = 5,
    cell_size: float = 0.5,
    seed: int | None = None,
    max_steps: int = 50_000,
    dt: float = 1 / 240,
    gui: bool = False,
    verbose: bool = True,
) -> bool:
    """Run the maze-solving simulation.

    Args:
        rows: Maze rows.
        cols: Maze columns.
        cell_size: Cell side length in metres.
        seed: Maze RNG seed.
        max_steps: Maximum physics steps before giving up.
        dt: Physics timestep (default PyBullet 1/240).
        gui: Open the PyBullet viewer.
        verbose: Print progress.

    Returns:
        True if the robot reached the goal, False if it timed out.
    """
    world = World(rows=rows, cols=cols, cell_size=cell_size, seed=seed, gui=gui)

    sensor = RaySensor(
        client=world.client,
        robot_id=world.robot.body_id,
        num_rays=7,
        max_range=1.0,
    )
    controller = WallFollower()

    gx, gy = world.goal_position
    reached = False
    report_every = max(1, max_steps // 20)

    try:
        for step in range(max_steps):
            rays = sensor.read()
            cmd = controller.compute(rays)
            world.robot.set_wheel_velocities(cmd.left, cmd.right)
            world.step()

            if gui:
                _time.sleep(dt)

            if step % report_every == 0 and verbose:
                rx, ry, yaw = world.robot.get_pose()
                print(
                    f"step {step:6d} | pos=({rx:6.2f}, {ry:6.2f}) "
                    f"| goal=({gx:.2f}, {gy:.2f}) | front={rays[len(rays)//2]:.2f}m"
                )

            if world.is_at_goal():
                rx, ry, _ = world.robot.get_pose()
                if verbose:
                    print(f"  -> Reached goal at step {step}! pos=({rx:.2f}, {ry:.2f})")
                reached = True
                break

        if not reached and verbose:
            rx, ry, _ = world.robot.get_pose()
            print(f"  -> Timed out after {max_steps} steps. pos=({rx:.2f}, {ry:.2f})")

    finally:
        if not gui:
            world.close()

    return reached


if __name__ == "__main__":
    run_simulation(gui=False, verbose=True)
