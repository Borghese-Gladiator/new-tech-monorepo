Claude read the ChatGPT plan and generated this implementation plan

# Maze Navigator Robot - Implementation Plan

## Brief
Implement a 2-wheeled differential-drive robot in MuJoCo that navigates a procedurally generated maze using a left-hand-rule wall follower with ray-cast sensors.

## Changes
- `config/sim_config.yaml` - runtime configuration (speeds, gains, maze params)
- `config/robot.xml` - robot MJCF fragment (inline generation, not static file)
- `src/main.py` - entry point, loads config, runs simulation
- `src/robot_interface.py` - differential drive robot model + MJCF generation
- `src/controller.py` - wall-following navigation logic
- `src/sensors.py` - ray-cast distance sensor abstraction
- `src/maze_env.py` - maze generation, MJCF walls, goal detection, episode state
- `src/utils.py` - config loading, angle math helpers

## Tests
### Unit
- test_maze_env: maze generation produces valid perfect maze, BFS reachability
- test_controller: wall follower outputs correct commands for known ray patterns
- test_sensors: ray sensor returns max_range when no obstacles

### Manual
- `poetry run python src/main.py` — robot should navigate maze and print progress
- `poetry run python src/main.py --gui` — visual confirmation of robot movement
- `poetry run python src/main.py --headless --seed 42` — deterministic run, should reach goal
