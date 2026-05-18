"""start subcommand. Transitions ready -> building. Creates the worktree."""
from __future__ import annotations

import pathlib

from lib import metadata, transitions, locks, repos, run_ids
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Approve the plan and create the worktree."


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--approved-by", required=True)


def run(args) -> int:
    cfg = load_config(args)
    actor = actor_from_env("human")
    actor["name"] = args.approved_by
    run_id = args.run_id

    try:
        meta = metadata.load(cfg, run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    if meta["status"] != "ready":
        return fail(f"start requires status=ready, got {meta['status']!r}", 2)

    rd = metadata.run_dir(cfg, run_id)
    # Re-verify pre-impl artifacts.
    for name in ("brief.md", "plan.md", "preflight.md", "assumptions.md", "decisions.md"):
        p = rd / name
        if not p.exists() or not p.read_text().strip():
            return fail(f"required pre-impl artifact missing or empty: {p}", 2)

    repo_path = pathlib.Path(meta["target"]["repo"]["path"])
    repo_name = meta["target"]["repo"]["name"]
    base_ref = meta["target"]["repo"]["base_ref"]
    branch_name = meta["target"]["worktree"]["branch_name"]
    worktree_name = meta["target"]["worktree"]["name"]
    worktree_path = run_ids.make_worktree_path(cfg, repo_name, worktree_name)

    # Create the worktree.
    try:
        repos.create_worktree(repo_path, branch_name, worktree_path, base_ref)
    except repos.RepoError as e:
        return fail(f"failed to create worktree: {e}", 2)

    # Reflect in metadata.
    def _m(d):
        d["target"]["worktree"]["path"] = str(worktree_path)
        d["target"]["worktree"]["created"] = True
    metadata.update(cfg, run_id, _m)

    # Transition.
    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "building",
                evidence={
                    "approved_by": args.approved_by,
                    "repo_path": str(repo_path),
                    "repo_name": repo_name,
                    "base_ref": base_ref,
                    "branch_name": branch_name,
                    "worktree_name": worktree_name,
                    "worktree_path": str(worktree_path),
                    "preflight_path": str(rd / "preflight.md"),
                    "repo_mode": meta["target"]["repo"]["mode"],
                },
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)

    print(f"{run_id}: ready -> building")
    print(f"worktree: {worktree_path}")
    return 0
