"""Entry point: launch the PyBullet maze-solving simulation."""

import argparse

from sim.runner import run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description="Differential-drive robot maze solver")
    parser.add_argument("--rows", type=int, default=5, help="Maze rows (default 5)")
    parser.add_argument("--cols", type=int, default=5, help="Maze columns (default 5)")
    parser.add_argument("--cell-size", type=float, default=0.5, help="Cell size in metres (default 0.5)")
    parser.add_argument("--seed", type=int, default=None, help="Maze RNG seed")
    parser.add_argument("--max-steps", type=int, default=100_000, help="Max physics steps")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    args = parser.parse_args()

    reached = run_simulation(
        rows=args.rows,
        cols=args.cols,
        cell_size=args.cell_size,
        seed=args.seed,
        max_steps=args.max_steps,
        gui=not args.headless,
        verbose=True,
    )
    if reached:
        print("\nMaze solved!")
    else:
        print("\nDid not reach goal in time.")


if __name__ == "__main__":
    main()
