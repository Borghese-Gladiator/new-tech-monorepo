After generating standalone simulations with MuJoCo, I wanted to run MuJoCo with a real world problem.

```
poetry install
eval $(poetry env activate)  # MacOS for Poetry
mjpython src.main
```

# MuJoCo Maze Runner

A 2-wheeled differential-drive robot that autonomously navigates procedurally generated mazes in MuJoCo simulation. Uses ray-cast sensors and a left-hand-rule wall-following controller.

## Project Structure

```
├── config/
│   └── sim_config.yaml       # All tuneable parameters (maze, robot, sensors, controller, sim)
├── src/
│   ├── main.py                # Entry point, World class, simulation loop
│   ├── maze_env.py            # Maze generation (recursive backtracker DFS) + MJCF walls
│   ├── robot_interface.py     # Differential-drive robot MJCF + runtime interface
│   ├── sensors.py             # Ray-cast distance sensors via mj_ray
│   ├── controller.py          # Left-hand-rule wall follower with state machine
│   └── utils.py               # Config loading (YAML), quaternion-to-yaw
├── tests/
│   ├── test_maze_env.py       # Maze generation and validation tests
│   └── test_controller.py     # Controller behaviour tests
├── config/sim_config.yaml     # Runtime configuration
├── pyproject.toml             # Poetry project definition
└── archive/                   # Previous iteration (reference only)
```

## Setup

Requires Python 3.11.

```bash
poetry install
```

## Running

```bash
# Headless 5x5 maze (default)
poetry run python -m src.main --headless --seed 42

# With MuJoCo GUI viewer
poetry run python -m src.main --gui --seed 42

# Smaller 3x3 maze, faster solve
poetry run python -m src.main --headless --seed 42 --rows 3 --cols 3

# More steps for larger mazes
poetry run python -m src.main --headless --seed 42 --max-steps 500000

# Custom config file
poetry run python -m src.main --config path/to/config.yaml
```

## Tests

```bash
poetry run pytest tests/ -v
```

## How It Works

### Maze Generation
Recursive backtracker (DFS) produces a perfect maze where every cell is reachable from every other cell. Walls are converted to MJCF box geoms positioned and rotated in the world.

### Robot
- Chassis: 0.30 x 0.20 x 0.05 m box, 1.0 kg
- Two drive wheels: radius 0.04 m, velocity-controlled
- Rear caster sphere for stability
- Free joint allows unconstrained 6-DOF movement

### Sensors
7 ray-cast beams spread across 180 degrees (left to right). Each ray returns distance to the nearest wall, up to 1.0 m max range. Rays originate at chassis height and exclude the robot's own body.

### Controller
State-machine wall follower with two states:
- **FOLLOW_WALL**: Drive forward, using proportional control to maintain desired distance from the left wall. If no left wall is detected, turn left to find one.
- **TURN_RIGHT**: Rotate right in-place when front is blocked. Stays in this state until front clears a hysteresis threshold (prevents oscillation).

### Configuration
All parameters live in `config/sim_config.yaml`:
- **maze**: rows, cols, cell_size, seed, wall dimensions
- **robot**: wheel_radius, wheelbase, chassis size, max speed, actuator gain
- **sensors**: ray count, max range, field of view
- **controller**: wall distance, thresholds, speeds, proportional gain
- **simulation**: timestep, max steps, goal tolerance

CLI flags (`--rows`, `--cols`, `--seed`, `--max-steps`) override the corresponding config values.
