"""Maze generation and PyBullet wall spawning."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import pybullet as p


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

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(self, seed: int | None = None) -> None:
        """Generate a perfect maze using recursive backtracker (DFS).

        Every cell is reachable from every other cell (no isolated regions).
        """
        rng = random.Random(seed)
        R, C = self.rows, self.cols
        cs = self.cell_size

        # Track which walls exist between cells.
        # h_walls[r][c] = True means there is a horizontal wall on the SOUTH
        # side of cell (r, c), i.e., between row r and row r+1.
        # v_walls[r][c] = True means there is a vertical wall on the EAST
        # side of cell (r, c).
        h_walls = [[True] * C for _ in range(R + 1)]  # R+1 rows of horizontal walls
        v_walls = [[True] * (C + 1) for _ in range(R)]  # C+1 cols of vertical walls

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
            # Remove wall between (r,c) and (nr,nc)
            if dr == -1:  # neighbour is NORTH → remove top wall of current
                h_walls[r][c] = False
            elif dr == 1:  # neighbour is SOUTH → remove bottom wall of current
                h_walls[r + 1][c] = False
            elif dc == -1:  # neighbour is WEST → remove left wall of current
                v_walls[r][c] = False
            elif dc == 1:  # neighbour is EAST → remove right wall of current
                v_walls[r][c + 1] = False

            visited[nr][nc] = True
            stack.append((nr, nc))

        # Convert wall grids to WallSegment list
        self.walls.clear()

        # Horizontal walls
        for r in range(R + 1):
            for c in range(C):
                if h_walls[r][c]:
                    x1 = c * cs
                    x2 = (c + 1) * cs
                    y = r * cs
                    self.walls.append(WallSegment(x1, y, x2, y))

        # Vertical walls
        for r in range(R):
            for c in range(C + 1):
                if v_walls[r][c]:
                    x = c * cs
                    y1 = r * cs
                    y2 = (r + 1) * cs
                    self.walls.append(WallSegment(x, y1, x, y2))

        self.goal = (R - 1, C - 1)

    # ------------------------------------------------------------------
    # Spawning in PyBullet
    # ------------------------------------------------------------------

    def spawn(self, client: int, wall_height: float = 0.15, wall_thickness: float = 0.02) -> list[int]:
        """Create collision/visual boxes in PyBullet for every wall segment.

        Returns list of body IDs for the spawned walls.
        """
        body_ids: list[int] = []
        for seg in self.walls:
            cx = (seg.x1 + seg.x2) / 2
            cy = (seg.y1 + seg.y2) / 2
            dx = seg.x2 - seg.x1
            dy = seg.y2 - seg.y1
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length < 1e-6:
                continue

            half_extents = [length / 2, wall_thickness / 2, wall_height / 2]

            import math
            angle = math.atan2(dy, dx)
            orn = p.getQuaternionFromEuler([0, 0, angle])

            col_id = p.createCollisionShape(
                p.GEOM_BOX, halfExtents=half_extents, physicsClientId=client
            )
            vis_id = p.createVisualShape(
                p.GEOM_BOX, halfExtents=half_extents,
                rgbaColor=[0.6, 0.6, 0.6, 1.0], physicsClientId=client
            )
            body_id = p.createMultiBody(
                baseMass=0,  # static
                baseCollisionShapeIndex=col_id,
                baseVisualShapeIndex=vis_id,
                basePosition=[cx, cy, wall_height / 2],
                baseOrientation=orn,
                physicsClientId=client,
            )
            body_ids.append(body_id)

        return body_ids

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

        # Rebuild adjacency from wall segments for validation
        blocked: set[tuple[float, float, float, float]] = set()
        for w in self.walls:
            blocked.add((round(w.x1, 6), round(w.y1, 6), round(w.x2, 6), round(w.y2, 6)))

        def wall_between(r1: int, c1: int, r2: int, c2: int) -> bool:
            dr, dc = r2 - r1, c2 - c1
            if dr == -1:  # north
                x1, x2 = c1 * cs, (c1 + 1) * cs
                y = r1 * cs
            elif dr == 1:  # south
                x1, x2 = c1 * cs, (c1 + 1) * cs
                y = (r1 + 1) * cs
            elif dc == -1:  # west
                x = c1 * cs
                y1, y2 = r1 * cs, (r1 + 1) * cs
                return (round(x, 6), round(y1, 6), round(x, 6), round(y2, 6)) in blocked
            elif dc == 1:  # east
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
