"""Unit tests for the RSSI-to-distance utility."""

import math
import pytest
from sensors.rssi import rssi_to_distance


@pytest.mark.parametrize("rssi,tx_power,n,expected_distance", [
    # At 1 m: rssi == tx_power → distance = 10^0 = 1.0
    (-59.0, -59.0, 2.0, 1.0),
    # At 10 m (free-space, n=2): rssi = tx_power - 10*n*log10(10) = -59 - 20 = -79
    (-79.0, -59.0, 2.0, 10.0),
    # At 2 m (n=2): rssi = -59 - 20*log10(2) ≈ -59 - 6.02 = -65.02
    (-65.02, -59.0, 2.0, 2.0),
    # Higher path loss exponent n=3, still 1 m → distance = 1.0
    (-59.0, -59.0, 3.0, 1.0),
    # tx_power=-70, rssi=-70 at 1 m
    (-70.0, -70.0, 2.0, 1.0),
])
def test_rssi_to_distance(rssi, tx_power, n, expected_distance):
    result = rssi_to_distance(rssi, tx_power=tx_power, n=n)
    assert math.isclose(result, expected_distance, rel_tol=1e-2), (
        f"Expected {expected_distance}, got {result}"
    )


def test_invalid_n_raises():
    with pytest.raises(ValueError):
        rssi_to_distance(-70.0, n=0)
