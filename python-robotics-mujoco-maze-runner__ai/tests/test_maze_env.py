"""Tests for maze generation and validation."""

import pytest

from src.maze_env import Maze


@pytest.mark.parametrize(
    "rows,cols,seed",
    [
        (3, 3, 0),
        (5, 5, 42),
        (7, 7, 123),
        (4, 6, 99),
        (10, 10, 7),
    ],
)
def test_generated_maze_is_valid(rows: int, cols: int, seed: int) -> None:
    """Every cell should be reachable from (0,0) in a perfect maze."""
    maze = Maze(rows=rows, cols=cols, cell_size=0.5)
    maze.generate(seed=seed)
    assert maze.is_valid()


def test_goal_is_bottom_right() -> None:
    maze = Maze(rows=5, cols=5, cell_size=0.5)
    maze.generate(seed=0)
    assert maze.goal == (4, 4)


def test_cell_centre() -> None:
    maze = Maze(rows=3, cols=3, cell_size=1.0)
    assert maze.cell_centre(0, 0) == (0.5, 0.5)
    assert maze.cell_centre(2, 2) == (2.5, 2.5)


def test_deterministic_generation() -> None:
    """Same seed should produce identical wall layouts."""
    m1 = Maze(rows=5, cols=5, cell_size=0.5)
    m1.generate(seed=42)
    m2 = Maze(rows=5, cols=5, cell_size=0.5)
    m2.generate(seed=42)

    assert len(m1.walls) == len(m2.walls)
    for w1, w2 in zip(m1.walls, m2.walls):
        assert (w1.x1, w1.y1, w1.x2, w1.y2) == (w2.x1, w2.y1, w2.x2, w2.y2)


def test_walls_mjcf_produces_xml() -> None:
    maze = Maze(rows=3, cols=3, cell_size=0.5)
    maze.generate(seed=0)
    xml = maze.walls_mjcf()
    assert "wall_" in xml
    assert "geom" in xml
