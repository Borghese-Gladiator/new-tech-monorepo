"""Maze generation, MJCF wall geometry, and episode state."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class WallSegment:
    """A wall defined by its two endpoints (2-D, z=0 ground plane)."""
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class Maze:
    """Grid maze generated via recursive backtracker.

    Attributes:
        rows: Number of cell rows.
        cols: Number of cell columns.
        cell_size: Side length of each square cell (metres).
        walls: List of wall segments after generation.
        goal: (row, col) index of the goal cell.
    """
    rows: int
    cols: int
    cell_size: float
    walls: list[WallSegment] = field(default_factory=list)
    goal: tuple[int, int] = (0, 0)

    def generate(self, seed: int | None = None) -> None:
        """Generate a perfect maze using recursive backtracker (DFS)."""
        rng = random.Random(seed)
        R, C = self.rows, self.cols
        cs = self.cell_size

        h_walls = [[True] * C for _ in range(R + 1)]
        v_walls = [[True] * (C + 1) for _ in range(R)]

        visited = [[False] * C for _ in range(R)]
        stack: list[tuple[int, int]] = [(0, 0)]
        visited[0][0] = True

        while stack:
            r, c = stack[-1]
            neighbours = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and not visited[nr][nc]:
                    neighbours.append((nr, nc, dr, dc))

            if not neighbours:
                stack.pop()
                continue

            nr, nc, dr, dc = rng.choice(neighbours)
            if dr == -1:
                h_walls[r][c] = False
            elif dr == 1:
                h_walls[r + 1][c] = False
            elif dc == -1:
                v_walls[r][c] = False
            elif dc == 1:
                v_walls[r][c + 1] = False

            visited[nr][nc] = True
            stack.append((nr, nc))

        self.walls.clear()

        for r in range(R + 1):
            for c in range(C):
                if h_walls[r][c]:
                    x1 = c * cs
                    x2 = (c + 1) * cs
                    y = r * cs
                    self.walls.append(WallSegment(x1, y, x2, y))

        for r in range(R):
            for c in range(C + 1):
                if v_walls[r][c]:
                    x = c * cs
                    y1 = r * cs
                    y2 = (r + 1) * cs
                    self.walls.append(WallSegment(x, y1, x, y2))

        self.goal = (R - 1, C - 1)

    def walls_mjcf(
        self, wall_height: float = 0.15, wall_thickness: float = 0.02
    ) -> str:
        """Return MJCF XML geom elements for every wall segment."""
        lines: list[str] = []
        for i, seg in enumerate(self.walls):
            cx = (seg.x1 + seg.x2) / 2
            cy = (seg.y1 + seg.y2) / 2
            dx = seg.x2 - seg.x1
            dy = seg.y2 - seg.y1
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length < 1e-6:
                continue

            angle = math.degrees(math.atan2(dy, dx))
            half_len = length / 2
            half_thick = wall_thickness / 2
            half_height = wall_height / 2

            lines.append(
                f'    <geom name="wall_{i}" type="box" '
                f'pos="{cx} {cy} {half_height}" '
                f'euler="0 0 {angle}" '
                f'size="{half_len} {half_thick} {half_height}" '
                f'rgba="0.6 0.6 0.6 1.0"/>'
            )
        return "\n".join(lines)

    def cell_centre(self, row: int, col: int) -> tuple[float, float]:
        """Return (x, y) world position of a cell's centre."""
        x = (col + 0.5) * self.cell_size
        y = (row + 0.5) * self.cell_size
        return x, y

    def goal_position(self) -> tuple[float, float]:
        """Centre of the goal cell in world coordinates."""
        return self.cell_centre(*self.goal)

    def is_valid(self) -> bool:
        """BFS reachability check — True if every cell is reachable from (0,0)."""
        R, C = self.rows, self.cols
        cs = self.cell_size

        blocked: set[tuple[float, float, float, float]] = set()
        for w in self.walls:
            blocked.add((round(w.x1, 6), round(w.y1, 6), round(w.x2, 6), round(w.y2, 6)))

        def wall_between(r1: int, c1: int, r2: int, c2: int) -> bool:
            dr, dc = r2 - r1, c2 - c1
            if dr == -1:
                x1, x2 = c1 * cs, (c1 + 1) * cs
                y = r1 * cs
            elif dr == 1:
                x1, x2 = c1 * cs, (c1 + 1) * cs
                y = (r1 + 1) * cs
            elif dc == -1:
                x = c1 * cs
                y1, y2 = r1 * cs, (r1 + 1) * cs
                return (round(x, 6), round(y1, 6), round(x, 6), round(y2, 6)) in blocked
            elif dc == 1:
                x = (c1 + 1) * cs
                y1, y2 = r1 * cs, (r1 + 1) * cs
                return (round(x, 6), round(y1, 6), round(x, 6), round(y2, 6)) in blocked
            else:
                return True
            return (round(x1, 6), round(y, 6), round(x2, 6), round(y, 6)) in blocked

        visited = [[False] * C for _ in range(R)]
        queue = [(0, 0)]
        visited[0][0] = True
        count = 1

        while queue:
            r, c = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and not visited[nr][nc]:
                    if not wall_between(r, c, nr, nc):
                        visited[nr][nc] = True
                        count += 1
                        queue.append((nr, nc))

        return count == R * C
