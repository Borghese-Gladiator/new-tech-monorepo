"""abandon subcommand. Wildcard: any non-terminal -> abandoned."""
from __future__ import annotations

from lib import metadata, transitions, locks
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Abandon a run. Wildcard from any non-terminal state."


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--reason", required=True)
    p.add_argument("--abandoned-by", required=True)


def run(args) -> int:
    cfg = load_config(args)
    actor = actor_from_env("human")
    actor["name"] = args.abandoned_by
    run_id = args.run_id

    try:
        meta = metadata.load(cfg, run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    if transitions.is_terminal(cfg, meta["status"]):
        return fail(f"cannot abandon from terminal state {meta['status']!r}", 2)

    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "abandoned",
                evidence={
                    "abandoned_reason": args.reason,
                    "abandoned_by": args.abandoned_by,
                },
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)

    def _m(d):
        d["completion"]["abandoned_reason"] = args.reason
    metadata.update(cfg, run_id, _m)

    print(f"{run_id}: -> abandoned")
    print(f"reason: {args.reason}")
    return 0
