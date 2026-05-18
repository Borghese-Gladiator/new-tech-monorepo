"""bounce subcommand. human_review -> building."""
from __future__ import annotations

from lib import metadata, transitions, locks
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Bounce a run from human_review back to building."


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--reason", required=True)
    p.add_argument("--requested-by", required=True)


def run(args) -> int:
    cfg = load_config(args)
    actor = actor_from_env("human")
    actor["name"] = args.requested_by
    run_id = args.run_id

    try:
        meta = metadata.load(cfg, run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    if meta["status"] != "human_review":
        return fail(f"bounce requires status=human_review, got {meta['status']!r}", 2)

    rd = metadata.run_dir(cfg, run_id)
    handoff_path = rd / "handoff.md"

    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "building",
                evidence={
                    "bounce_reason": args.reason,
                    "requested_by": args.requested_by,
                    "handoff_path": str(handoff_path),
                },
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)

    print(f"{run_id}: human_review -> building")
    print(f"reason: {args.reason}")
    return 0
