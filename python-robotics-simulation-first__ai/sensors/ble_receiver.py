"""BLE receiver interface and shared data types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BLEReading:
    """A single BLE advertisement reading."""
    address: str
    rssi: float        # dBm
    tx_power: float    # dBm, calibrated at 1 m


class BLEReceiver(ABC):
    """Abstract interface for BLE receivers (simulated or real)."""

    @abstractmethod
    def read(self) -> BLEReading:
        """Return the latest BLE reading from the target beacon."""
