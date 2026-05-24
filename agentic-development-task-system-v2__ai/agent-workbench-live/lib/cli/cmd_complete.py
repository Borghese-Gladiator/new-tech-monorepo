"""complete subcommand. human_review -> done."""
from __future__ import annotations

from lib import metadata, transitions, locks
from lib.cli._common import actor_from_env, fail, load_config
from lib.metrics import writer as metrics_writer


HELP = "Accept a run in human_review; transition to done."


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--accepted-by", required=True)
    p.add_argument("--completion-ref", help="Defaults to local-branch:<branch_name>.")


def run(args) -> int:
    cfg = load_config(args)
    actor = actor_from_env("human")
    actor["name"] = args.accepted_by
    run_id = args.run_id

    try:
        meta = metadata.load(cfg, run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    if meta["status"] != "human_review":
        return fail(f"complete requires status=human_review, got {meta['status']!r}", 2)

    rd = metadata.run_dir(cfg, run_id)
    audit_path = rd / "audit.md"
    if not audit_path.exists():
        return fail(f"audit.md missing at {audit_path}; re-run validate", 2)

    branch_name = meta["target"]["worktree"]["branch_name"]
    completion_ref = args.completion_ref or f"local-branch:{branch_name}"

    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "done",
                evidence={
                    "accepted_by": args.accepted_by,
                    "completion_ref": completion_ref,
                    "audit_path": str(audit_path),
                },
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)

    # Record completion in metadata.
    def _m(d):
        d["completion"]["accepted_by"] = args.accepted_by
        d["completion"]["completion_ref"] = completion_ref
        d["completion"]["completed_at"] = metadata.now_iso()
    metadata.update(cfg, run_id, _m)

    # Token-efficiency tracking: refresh metrics.jsonl at terminal boundary.
    # Best-effort — never raises into the caller.
    try:
        metrics_writer.record_run_metrics(cfg, run_id)
    except Exception:
        pass

    print(f"{run_id}: human_review -> done")
    print(f"completion_ref: {completion_ref}")
    return 0
