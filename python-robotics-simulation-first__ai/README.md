# Python Robotics Simulation — BLE Beacon Follower

A modular 2D robotics simulation where a robot navigates toward a BLE beacon using RSSI-derived distance estimates and a proportional controller.

## Architecture

```
sensors/
  ble_receiver.py      # BLEReceiver ABC + BLEReading dataclass
  rssi.py              # rssi_to_distance() — log-distance path loss model
  simulated_ble.py     # SimulatedBLEReceiver — geometric RSSI + Gaussian noise
  real_ble.py          # RealBLEReceiver — Bleak async scan, sync wrapper

sim/
  robot.py             # Robot — 2D point with move() and turn()
  world.py             # World — holds beacon position and robot
  runner.py            # run_simulation() loop + __main__ entry point

control/
  controller.py        # BeaconFollower — P-controller for speed and heading

tests/
  test_rssi.py         # RSSI ↔ distance round-trip, edge cases
  test_controller.py   # Speed proportionality, turn direction, max-speed cap
  test_simulation.py   # End-to-end: robot reaches beacon within 0.5 m
```

## How it works

1. **RSSI → distance**: `rssi_to_distance` uses the log-distance path loss model: `d = 10 ^ ((tx_power - rssi) / (10 * n))`
2. **Simulated BLE**: `SimulatedBLEReceiver` computes geometric distance between robot and beacon, converts to RSSI, and adds Gaussian noise.
3. **Controller**: `BeaconFollower` computes forward speed proportional to `distance - goal_distance` and a heading correction from the bearing to the beacon.
4. **Runner**: Each tick — read BLE → compute command → turn robot → move robot.

## Quickstart

```bash
# Install dependencies
poetry install

# Run the simulation (beacon at (5,5), robot starts at (0,0))
poetry run python -m sim.runner

# Run tests
poetry run pytest -v
```

## Example output

```
step   0 | pos=(  0.15,   0.02) | dist=6.95m | speed=1.50 | turn=1.57
step   1 | pos=(  0.29,   0.07) | dist=6.82m | speed=1.50 | turn=1.28
...
step  99 | pos=(  4.81,   4.77) | dist=0.30m | speed=0.01 | turn=0.00
  -> Reached beacon at step 99!

Final distance to beacon: 0.299 m
```

## Using a real BLE beacon

```bash
# Scan for a specific beacon by MAC address
poetry run python -m sensors.real_ble AA:BB:CC:DD:EE:FF
```

Replace `AA:BB:CC:DD:EE:FF` with your beacon's address. On macOS, Bleak uses UUIDs instead of MAC addresses.

## Configuration

Key parameters in `run_simulation()` and `BeaconFollower`:

| Parameter       | Default | Description                              |
|-----------------|---------|------------------------------------------|
| `kp`            | `0.8`   | Proportional gain for forward speed      |
| `max_speed`     | `1.5`   | Speed cap (m/s)                          |
| `goal_distance` | `0.3`   | Stop distance from beacon (m)            |
| `k_turn`        | `2.0`   | Proportional gain for heading correction |
| `noise_std`     | `0.5`   | Simulated RSSI noise std dev (dBm)       |
| `n`             | `2.0`   | Path loss exponent (2 = free space)      |

## Requirements

- Python 3.11+
- numpy
- bleak
- pytest
