"""Unit tests for maze generation."""

import pytest
from sim.maze import Maze


@pytest.mark.parametrize("rows,cols,seed", [
    (3, 3, 0),
    (5, 5, 42),
    (8, 8, 99),
    (4, 6, 7),
])
def test_maze_is_valid(rows, cols, seed):
    """Every cell should be reachable from (0,0) — perfect maze property."""
    maze = Maze(rows=rows, cols=cols, cell_size=0.5)
    maze.generate(seed=seed)
    assert maze.is_valid(), f"Maze {rows}x{cols} seed={seed} has unreachable cells"


def test_maze_deterministic():
    """Same seed produces identical wall sets."""
    a = Maze(rows=5, cols=5, cell_size=0.5)
    a.generate(seed=123)
    b = Maze(rows=5, cols=5, cell_size=0.5)
    b.generate(seed=123)

    walls_a = {(w.x1, w.y1, w.x2, w.y2) for w in a.walls}
    walls_b = {(w.x1, w.y1, w.x2, w.y2) for w in b.walls}
    assert walls_a == walls_b


def test_maze_different_seeds_differ():
    """Different seeds produce different mazes (extremely likely)."""
    a = Maze(rows=5, cols=5, cell_size=0.5)
    a.generate(seed=1)
    b = Maze(rows=5, cols=5, cell_size=0.5)
    b.generate(seed=2)

    walls_a = {(w.x1, w.y1, w.x2, w.y2) for w in a.walls}
    walls_b = {(w.x1, w.y1, w.x2, w.y2) for w in b.walls}
    assert walls_a != walls_b


def test_maze_boundary_walls_present():
    """Outer boundary should be fully walled."""
    maze = Maze(rows=3, cols=3, cell_size=1.0)
    maze.generate(seed=0)

    wall_set = {(round(w.x1, 6), round(w.y1, 6), round(w.x2, 6), round(w.y2, 6))
                for w in maze.walls}

    # Top boundary: y=0, segments (0,0)→(1,0), (1,0)→(2,0), (2,0)→(3,0)
    for c in range(3):
        seg = (round(c * 1.0, 6), 0.0, round((c + 1) * 1.0, 6), 0.0)
        assert seg in wall_set, f"Missing top boundary segment {seg}"

    # Bottom boundary: y=3
    for c in range(3):
        seg = (round(c * 1.0, 6), 3.0, round((c + 1) * 1.0, 6), 3.0)
        assert seg in wall_set, f"Missing bottom boundary segment {seg}"


def test_goal_cell():
    maze = Maze(rows=5, cols=5, cell_size=0.5)
    maze.generate(seed=0)
    assert maze.goal == (4, 4)
    gx, gy = maze.goal_position()
    assert gx == pytest.approx(2.25)
    assert gy == pytest.approx(2.25)
