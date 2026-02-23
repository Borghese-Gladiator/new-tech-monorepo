"""Simulated quadrature wheel encoder."""

from __future__ import annotations

import math


class Encoder:
    """Simulated wheel encoder that accumulates ticks from wheel angle changes.

    Ticks increment for forward rotation and decrement for reverse.

    Args:
        ticks_per_rev: Number of encoder ticks per full wheel revolution.

    Attributes:
        cumulative: Total signed ticks accumulated since construction.
    """

    def __init__(self, ticks_per_rev: int = 360) -> None:
        if ticks_per_rev <= 0:
            raise ValueError(f"ticks_per_rev must be positive, got {ticks_per_rev}")
        self.ticks_per_rev = ticks_per_rev
        self._ticks_per_rad: float = ticks_per_rev / (2.0 * math.pi)
        self.cumulative: int = 0
        self._delta_accum: float = 0.0   # fractional ticks not yet committed
        self._delta_since_read: int = 0  # ticks since last read_delta()

    def update(self, delta_rad: float) -> None:
        """Accumulate ticks for a wheel rotation of delta_rad radians.

        Args:
            delta_rad: Signed wheel rotation this timestep (rad).
                       Positive = forward, negative = reverse.
        """
        raw = delta_rad * self._ticks_per_rad + self._delta_accum
        ticks = int(math.trunc(raw))
        self._delta_accum = raw - ticks
        self.cumulative += ticks
        self._delta_since_read += ticks

    def read(self) -> int:
        """Return total cumulative signed ticks since construction."""
        return self.cumulative

    def read_delta(self) -> int:
        """Return signed ticks since the last call to read_delta(), then reset.

        On the first call returns ticks since construction.
        """
        delta = self._delta_since_read
        self._delta_since_read = 0
        return delta
