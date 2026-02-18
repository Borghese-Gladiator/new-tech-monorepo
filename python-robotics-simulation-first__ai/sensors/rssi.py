"""RSSI-to-distance conversion using the log-distance path loss model."""

import math


def rssi_to_distance(rssi: float, tx_power: float = -59.0, n: float = 2.0) -> float:
    """Convert RSSI (dBm) to estimated distance (metres).

    Uses the log-distance path loss model:
        distance = 10 ^ ((tx_power - rssi) / (10 * n))

    Args:
        rssi: Received signal strength in dBm (negative value, e.g. -70).
        tx_power: Calibrated RSSI at 1 metre (dBm). Default -59 dBm.
        n: Path loss exponent. Free space = 2.0; indoors typically 2–4.

    Returns:
        Estimated distance in metres (always positive).
    """
    if n <= 0:
        raise ValueError(f"Path loss exponent n must be positive, got {n}")
    return 10 ** ((tx_power - rssi) / (10.0 * n))
