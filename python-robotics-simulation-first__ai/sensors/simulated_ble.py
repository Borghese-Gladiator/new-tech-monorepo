"""Simulated BLE receiver that derives RSSI from robot/beacon positions."""

from __future__ import annotations

import math
from typing import Callable

import numpy as np

from sensors.ble_receiver import BLEReceiver, BLEReading
from sensors.rssi import rssi_to_distance


# Inverse of the log-distance model: distance → RSSI
def _distance_to_rssi(distance: float, tx_power: float, n: float) -> float:
    """Convert distance (m) to RSSI (dBm) using log-distance path loss model."""
    if distance <= 0:
        raise ValueError(f"distance must be positive, got {distance}")
    return tx_power - 10.0 * n * math.log10(distance)


class SimulatedBLEReceiver(BLEReceiver):
    """BLE receiver that simulates RSSI based on geometric distance.

    Args:
        beacon_position: Fixed (x, y) position of the beacon.
        robot_position_fn: Callable returning current robot (x, y) position.
        address: Simulated beacon MAC address.
        tx_power: Calibrated RSSI at 1 m (dBm).
        n: Path loss exponent.
        noise_std: Std dev of Gaussian noise added to RSSI (dBm).
        rng: Optional numpy random Generator for reproducibility.
    """

    def __init__(
        self,
        beacon_position: np.ndarray,
        robot_position_fn: Callable[[], np.ndarray],
        address: str = "AA:BB:CC:DD:EE:FF",
        tx_power: float = -59.0,
        n: float = 2.0,
        noise_std: float = 2.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        self._beacon = np.array(beacon_position, dtype=float)
        self._robot_pos = robot_position_fn
        self._address = address
        self._tx_power = tx_power
        self._n = n
        self._noise_std = noise_std
        self._rng = rng if rng is not None else np.random.default_rng()

    def read(self) -> BLEReading:
        robot_pos = np.array(self._robot_pos(), dtype=float)
        distance = float(np.linalg.norm(robot_pos - self._beacon))
        # Clamp to a minimum to avoid log(0)
        distance = max(distance, 0.01)
        rssi = _distance_to_rssi(distance, self._tx_power, self._n)
        rssi += float(self._rng.normal(0.0, self._noise_std))
        return BLEReading(address=self._address, rssi=rssi, tx_power=self._tx_power)
