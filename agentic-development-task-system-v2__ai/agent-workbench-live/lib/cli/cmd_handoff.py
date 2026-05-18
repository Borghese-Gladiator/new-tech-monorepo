"""handoff subcommand. Read-only. Re-display handoff info for a run."""
from __future__ import annotations

from lib import metadata
from lib.cli._common import fail, load_config


HELP = "Print handoff info (read-only)."


def register(p) -> None:
    p.add_argument("run_id")


def run(args) -> int:
    cfg = load_config(args)
    try:
        meta = metadata.load(cfg, args.run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    rd = metadata.run_dir(cfg, args.run_id)
    handoff = rd / "handoff.md"
    if not handoff.exists():
        return fail(f"handoff.md not yet produced for {args.run_id}", 2)

    print(f"# {args.run_id}")
    print(f"status:   {meta['status']}")
    print(f"branch:   {meta['target']['worktree']['branch_name']}")
    print(f"worktree: {meta['target']['worktree']['path']}")
    print(f"audit:    {rd / 'audit.md'}")
    print()
    print(handoff.read_text())
    return 0
