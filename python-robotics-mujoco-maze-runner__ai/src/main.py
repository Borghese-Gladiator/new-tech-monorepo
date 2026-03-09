"""Entry point: launch the MuJoCo maze-solving simulation."""

from __future__ import annotations

import argparse
import time as _time
from typing import Any

import mujoco

from src.utils import load_config
from src.maze_env import Maze
from src.robot_interface import DiffDriveRobot, RobotSpec, robot_mjcf, robot_actuators_mjcf
from src.sensors import RaySensor
from src.controller import WallFollower


class World:
    """Top-level simulation container."""

    def __init__(
        self,
        maze: Maze,
        robot_spec: RobotSpec,
        timestep: float = 0.001,
        wall_height: float = 0.25,
        wall_thickness: float = 0.06,
        gui: bool = False,
    ) -> None:
        self.maze = maze
        self._robot_spec = robot_spec
        self._timestep = timestep
        self._wall_height = wall_height
        self._wall_thickness = wall_thickness
        start_x, start_y = maze.cell_centre(0, 0)
        gx, gy = maze.goal_position()

        xml = self._build_mjcf(start_x, start_y, gx, gy)

        self.model = mujoco.MjModel.from_xml_string(xml)
        self.data = mujoco.MjData(self.model)

        free_jnt = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "chassis_free")
        qpos_adr = self.model.jnt_qposadr[free_jnt]
        self.data.qpos[qpos_adr] = start_x
        self.data.qpos[qpos_adr + 1] = start_y
        self.data.qpos[qpos_adr + 2] = robot_spec.chassis_z
        self.data.qpos[qpos_adr + 3] = 1.0

        mujoco.mj_forward(self.model, self.data)

        self.robot = DiffDriveRobot(
            model=self.model,
            data=self.data,
            max_wheel_speed=robot_spec.max_wheel_speed,
        )

        self._viewer = None
        if gui:
            from mujoco.viewer import launch_passive
            self._viewer = launch_passive(self.model, self.data)

    def _build_mjcf(
        self, start_x: float, start_y: float, goal_x: float, goal_y: float
    ) -> str:
        walls_xml = self.maze.walls_mjcf(
            wall_height=self._wall_height, wall_thickness=self._wall_thickness
        )
        r_xml = robot_mjcf(self._robot_spec)
        act_xml = robot_actuators_mjcf(self._robot_spec)

        return f"""\
<mujoco model="maze_world">
  <option gravity="0 0 -9.81" timestep="{self._timestep}" integrator="implicitfast"/>

  <default>
    <geom condim="3" friction="1.0 0.005 0.001"/>
  </default>

  <worldbody>
    <geom name="ground" type="plane" size="10 10 0.01"
          rgba="0.9 0.9 0.9 1" condim="4"
          friction="1.5 0.005 0.001"/>

{walls_xml}

    <geom name="goal_marker" type="cylinder" size="0.06 0.0025"
          pos="{goal_x} {goal_y} 0.005"
          rgba="0.1 0.9 0.1 0.8" contype="0" conaffinity="0"/>

{r_xml}
  </worldbody>

  <actuator>
{act_xml}
  </actuator>
</mujoco>
"""

    def step(self) -> None:
        mujoco.mj_step(self.model, self.data)
        if self._viewer is not None:
            self._viewer.sync()

    def is_at_goal(self, tolerance: float = 0.15) -> bool:
        rx, ry, _ = self.robot.get_pose()
        gx, gy = self.maze.goal_position()
        return ((rx - gx) ** 2 + (ry - gy) ** 2) ** 0.5 <= tolerance

    @property
    def goal_position(self) -> tuple[float, float]:
        return self.maze.goal_position()

    def close(self) -> None:
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None


def run_simulation(cfg: dict[str, Any], gui: bool = False, verbose: bool = True) -> bool:
    """Run the maze-solving simulation using the provided config."""
    mc = cfg["maze"]
    rc = cfg["robot"]
    sc = cfg["sensors"]
    cc = cfg["controller"]
    sim = cfg["simulation"]

    maze = Maze(rows=mc["rows"], cols=mc["cols"], cell_size=mc["cell_size"])
    maze.generate(seed=mc.get("seed"))

    robot_spec = RobotSpec(
        wheel_radius=rc["wheel_radius"],
        wheelbase=rc["wheelbase"],
        chassis_half_size=tuple(rc["chassis_half_size"]),
        max_wheel_speed=rc["max_wheel_speed"],
        actuator_kv=rc["actuator_kv"],
    )

    world = World(
        maze=maze,
        robot_spec=robot_spec,
        timestep=sim["timestep"],
        wall_height=mc.get("wall_height", 0.25),
        wall_thickness=mc.get("wall_thickness", 0.06),
        gui=gui,
    )

    sensor = RaySensor(
        model=world.model,
        data=world.data,
        num_rays=sc["num_rays"],
        max_range=sc["max_range"],
        fov=sc["fov"],
        ray_height=robot_spec.chassis_z,
    )
    controller = WallFollower(
        desired_wall_dist=cc["desired_wall_dist"],
        front_threshold=cc["front_threshold"],
        clear_threshold=cc["clear_threshold"],
        base_speed=cc["base_speed"],
        turn_speed=cc["turn_speed"],
        wall_kp=cc["wall_kp"],
    )

    max_steps = sim["max_steps"]
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
                _time.sleep(1 / 240)

            if step % report_every == 0 and verbose:
                rx, ry, yaw = world.robot.get_pose()
                print(
                    f"step {step:6d} | pos=({rx:6.2f}, {ry:6.2f}) "
                    f"| goal=({gx:.2f}, {gy:.2f}) | front={rays[len(rays)//2]:.2f}m"
                )

            if world.is_at_goal(tolerance=sim["goal_tolerance"]):
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Differential-drive robot maze solver")
    parser.add_argument("--config", type=str, default=None, help="Path to sim_config.yaml")
    parser.add_argument("--rows", type=int, default=None, help="Maze rows (overrides config)")
    parser.add_argument("--cols", type=int, default=None, help="Maze columns (overrides config)")
    parser.add_argument("--seed", type=int, default=None, help="Maze RNG seed (overrides config)")
    parser.add_argument("--max-steps", type=int, default=None, help="Max physics steps")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    parser.add_argument("--gui", action="store_true", help="Run with GUI viewer")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.rows is not None:
        cfg["maze"]["rows"] = args.rows
    if args.cols is not None:
        cfg["maze"]["cols"] = args.cols
    if args.seed is not None:
        cfg["maze"]["seed"] = args.seed
    if args.max_steps is not None:
        cfg["simulation"]["max_steps"] = args.max_steps

    gui = args.gui and not args.headless

    reached = run_simulation(cfg, gui=gui, verbose=True)
    if reached:
        print("\nMaze solved!")
    else:
        print("\nDid not reach goal in time.")


if __name__ == "__main__":
    main()
