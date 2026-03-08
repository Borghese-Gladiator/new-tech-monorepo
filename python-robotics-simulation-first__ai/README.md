# PyBullet Differential-Drive Maze Robot

A two-wheeled differential-drive robot that navigates procedurally generated mazes using ray-cast distance sensors and a left-hand-rule wall-following controller, all simulated in PyBullet.

## Architecture

```
src/maze_robot/              # installable Python package
  __init__.py                # re-exports DiffDriveRobot, WallFollower, RaySensor
  robot.py                   # DiffDriveRobot — inline URDF, wheel control, pose readback
  sensors/
    ray_sensor.py            # RaySensor — N ray-casts via pybullet.rayTestBatch
  control/
    controller.py            # WallFollower — left-hand-rule, outputs WheelCommand

sim/                         # simulation harness (depends on maze_robot)
  maze.py                    # Maze — recursive-backtracker generation, PyBullet wall spawning
  world.py                   # World — physics server, ground plane, maze, robot, goal marker
  runner.py                  # run_simulation() — sense → decide → act → step loop

main.py                      # CLI entry point (argparse)

tests/
  test_maze.py               # Maze validity, determinism, boundaries
  test_ray_sensor.py         # Empty-world max range, wall detection accuracy
  test_controller.py         # Turn-right/straight/turn-left behaviour
  test_robot.py              # Spawn position, forward motion, rotation
```

The `maze_robot` package contains the robot model, sensors, and control logic — no dependency on the simulation harness. The `sim/` directory wires everything together with PyBullet physics, maze generation, and the main loop.

## Robot Specification

| Property | Value |
|----------|-------|
| **Chassis** | Box: 0.30 m (L) x 0.20 m (W) x 0.05 m (H) |
| **Chassis mass** | 1.0 kg |
| **Drive wheels (x2)** | Cylinders: radius 0.04 m, width 0.02 m |
| **Wheel mass** | 0.1 kg each |
| **Wheelbase** | 0.22 m (centre-to-centre) |
| **Rear caster** | Sphere: radius 0.02 m, 0.05 kg, fixed to chassis |
| **Max wheel speed** | +/-10 rad/s |
| **Max wheel force** | 5 N-m |
| **Sensors** | 7 ray-cast beams, 180 deg FOV, 1.0 m max range |
| **Sensor height** | 0.065 m above ground (chassis centre) |

### Kinematics

Standard differential-drive forward kinematics:

```
v     = wheel_radius * (omega_left + omega_right) / 2        [m/s]
omega = wheel_radius * (omega_right - omega_left) / wheelbase [rad/s]
```

Where `omega_left` and `omega_right` are wheel angular velocities in rad/s.

### URDF Structure

```
chassis (base link)
  |-- left_wheel_joint  (continuous) → left_wheel
  |-- right_wheel_joint (continuous) → right_wheel
  |-- caster_joint      (fixed)      → caster
```

The URDF is generated programmatically (inline XML string) — no external files needed.

## How It Works

1. **Maze generation**: Recursive backtracker (DFS) creates a perfect maze — every cell is reachable from every other cell. Walls are spawned as static PyBullet box bodies.

2. **Sensing**: 7 rays fan out 180 deg from the robot's front. Each ray returns the distance to the nearest obstacle (wall), or `max_range` (1.0 m) if nothing is hit. Uses `pybullet.rayTestBatch`.

3. **Control**: Left-hand-rule wall follower:
   - Front blocked → turn right in place
   - No left wall → turn left (seek wall)
   - Left wall detected → proportional correction to maintain desired distance
   - Otherwise → drive straight

4. **Actuation**: Controller outputs `WheelCommand(left, right)` velocities in rad/s, applied to PyBullet joints via `VELOCITY_CONTROL`.

5. **Goal**: Robot starts at cell (0,0), goal is cell (rows-1, cols-1). Simulation ends when the robot reaches the goal cell centre within 0.15 m tolerance.

## Quickstart

```bash
# Install dependencies
poetry install

# Run with GUI (default 5x5 maze)
python main.py

# Run headless
python main.py --headless

# Custom maze
python main.py --rows 8 --cols 8 --seed 42

# Run tests
pytest -v
```

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--rows` | 5 | Maze row count |
| `--cols` | 5 | Maze column count |
| `--cell-size` | 0.5 | Cell side length in metres |
| `--seed` | None | RNG seed for maze generation |
| `--max-steps` | 100000 | Max physics steps before timeout |
| `--headless` | False | Run without PyBullet GUI |

## Configuration

Key tunable parameters in the source:

| Parameter | Location | Default | Description |
|-----------|----------|---------|-------------|
| `desired_wall_dist` | `WallFollower` | 0.20 m | Target distance from left wall |
| `front_threshold` | `WallFollower` | 0.22 m | Frontal obstacle turn trigger |
| `base_speed` | `WallFollower` | 5.0 rad/s | Forward wheel speed |
| `turn_speed` | `WallFollower` | 6.0 rad/s | In-place turn wheel speed |
| `wall_kp` | `WallFollower` | 15.0 | Proportional gain for wall tracking |
| `num_rays` | `RaySensor` | 7 | Number of sensor rays |
| `max_range` | `RaySensor` | 1.0 m | Maximum sensing distance |
| `fov` | `RaySensor` | pi (180 deg) | Total field of view |

## Requirements

- Python 3.11+
- numpy
- pybullet
- pytest
