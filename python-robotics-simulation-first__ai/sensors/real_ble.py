"""Real BLE receiver using the Bleak library."""

from __future__ import annotations

import asyncio

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from sensors.ble_receiver import BLEReceiver, BLEReading

# Fallback tx_power when the advertisement does not include one.
_DEFAULT_TX_POWER = -59.0


class RealBLEReceiver(BLEReceiver):
    """BLE receiver that scans for a specific beacon using Bleak.

    Args:
        target_address: MAC address (or UUID on macOS) of the beacon.
        scan_timeout: How long to scan before giving up (seconds).
        tx_power_fallback: Calibrated RSSI at 1 m if the beacon does not
                           advertise tx_power.
    """

    def __init__(
        self,
        target_address: str,
        scan_timeout: float = 5.0,
        tx_power_fallback: float = _DEFAULT_TX_POWER,
    ) -> None:
        self._address = target_address.upper()
        self._scan_timeout = scan_timeout
        self._tx_power_fallback = tx_power_fallback

    def read(self) -> BLEReading:
        """Synchronous wrapper around the async scan.

        Raises:
            RuntimeError: If the target beacon is not found within the timeout.
        """
        return asyncio.run(self._async_read())

    async def _async_read(self) -> BLEReading:
        found: dict[str, tuple[BLEDevice, AdvertisementData]] = {}

        def _callback(device: BLEDevice, adv: AdvertisementData) -> None:
            if device.address.upper() == self._address:
                found[device.address.upper()] = (device, adv)

        async with BleakScanner(detection_callback=_callback):
            await asyncio.sleep(self._scan_timeout)

        if self._address not in found:
            raise RuntimeError(
                f"Beacon {self._address} not found after {self._scan_timeout}s scan."
            )

        device, adv = found[self._address]
        rssi = float(adv.rssi if adv.rssi is not None else -100)
        tx_power = (
            float(adv.tx_power)
            if adv.tx_power is not None
            else self._tx_power_fallback
        )
        return BLEReading(address=device.address, rssi=rssi, tx_power=tx_power)


if __name__ == "__main__":
    import sys

    address = sys.argv[1] if len(sys.argv) > 1 else "AA:BB:CC:DD:EE:FF"
    print(f"Scanning for beacon: {address}")
    receiver = RealBLEReceiver(target_address=address, scan_timeout=5.0)
    try:
        reading = receiver.read()
        print(f"Reading: {reading}")
    except RuntimeError as e:
        print(f"Error: {e}")
