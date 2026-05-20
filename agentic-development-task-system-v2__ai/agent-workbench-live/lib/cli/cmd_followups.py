"""followups subcommand (TODO §1f).

Two modes:
  --init : while status=followups (wait — we enter followups via validate's
           default mode, so --init transitions validating -> followups). On
           --init we stage templates/follow-ups.md at the run root and apply
           the transition.
  default: while status=followups, validate the YAML-frontmatter entries in
           follow-ups.md, emit FollowupsRecorded + HumanHandoffCreated, and
           transition followups -> human_review (engine validates the
           HUMAN_REVIEW.md sections at that point).

Note: --init here is a convenience shortcut that does the same thing as
running `agent-workbench validate <run_id>` (which transitions validating
-> followups on staged runs). Most callers won't need --init; they'll come
in via /validate. We expose it anyway so /followups is symmetric with the
other stage commands.
"""
from __future__ import annotations

from lib import metadata, events, transitions, locks, lifecycle, followups as followups_mod
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Author follow-ups.md (--init stages template; default validates + transitions to human_review)."


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--init", action="store_true",
                   help="Stage follow-ups.md template and transition validating -> followups.")


def run(args) -> int:
    cfg = load_config(args)
    actor = actor_from_env("agent")
    run_id = args.run_id

    try:
        meta = metadata.load(cfg, run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    if not lifecycle.is_staged_run(cfg, run_id):
        return fail(
            f"followups stage exists for staged-layout runs only; {run_id} is flat",
            2,
        )

    rd = metadata.run_dir(cfg, run_id)

    if args.init:
        if meta["status"] != "validating":
            return fail(
                f"--init requires status=validating, got {meta['status']!r}", 2,
            )
        _stage_template(cfg, rd)
        try:
            with locks.acquire(cfg, run_id):
                transitions.transition(
                    cfg, run_id, "followups",
                    evidence={
                        "review_report_path": str(rd / "stages" / "validating" / "review.md"),
                        "qa_report_path": str(rd / "stages" / "validating" / "qa" / "report.md"),
                        "audit_path": str(rd / "audit.md"),
                    },
                    actor=actor,
                )
        except transitions.TransitionError as e:
            return fail(str(e), 4)
        print(f"{run_id}: validating -> followups; staged follow-ups.md at {rd / 'follow-ups.md'}")
        return 0

    # Default: followups -> human_review.
    if meta["status"] != "followups":
        return fail(
            f"default mode requires status=followups, got {meta['status']!r}", 2,
        )

    follow_path = rd / "follow-ups.md"
    if not follow_path.exists():
        return fail(f"follow-ups.md missing at {follow_path}", 2)
    text = follow_path.read_text()
    if not text.strip():
        return fail(f"follow-ups.md is empty at {follow_path}", 2)

    errors = followups_mod.validate(text)
    if errors:
        for e in errors:
            print(f"error: {e}")
        return fail(f"follow-ups.md failed validation ({len(errors)} issue(s))", 2)

    entries = followups_mod.extract_entries(text)
    cats = followups_mod.categories(entries)
    events.append(
        cfg, run_id, "FollowupsRecorded",
        payload={
            "followups_path": str(follow_path),
            "entry_count": len(entries),
            "categories": cats,
        },
        actor=actor,
    )

    # HUMAN_REVIEW.md is the reviewer entry point; the engine validates its
    # sections in transitions.transition() below.
    handoff_path = rd / "HUMAN_REVIEW.md"

    # Emit HumanHandoffCreated. Mirrors validate's flat-layout path; the
    # transition gate (engine-side) will reject if HUMAN_REVIEW.md is missing
    # or lacks the required headings.
    events.append(
        cfg, run_id, "HumanHandoffCreated",
        payload={
            "handoff_path": str(handoff_path),
            "branch_name": meta["target"]["worktree"]["branch_name"],
            "worktree_path": meta["target"]["worktree"]["path"],
            "review_report_path": str(rd / "stages" / "validating" / "review.md"),
            "qa_report_path": str(rd / "stages" / "validating" / "qa" / "report.md"),
            "audit_path": str(rd / "audit.md"),
        },
        actor=actor,
    )

    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "human_review",
                evidence={
                    "followups_path": str(follow_path),
                    "handoff_path": str(handoff_path),
                    "branch_name": meta["target"]["worktree"]["branch_name"],
                    "worktree_path": meta["target"]["worktree"]["path"],
                    "audit_path": str(rd / "audit.md"),
                    "entry_count": len(entries),
                },
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)

    # Reflect the (post-move) followups artifact path in metadata. The engine
    # already moved follow-ups.md into stages/followups/.
    def _m(d):
        d["artifacts"]["followups"] = "stages/followups/follow-ups.md"
    metadata.update(cfg, run_id, _m)

    print(f"{run_id}: followups -> human_review")
    print(f"entries:  {len(entries)} ({', '.join(cats) or 'none'})")
    return 0


def _stage_template(cfg, rd) -> None:
    dest = rd / "follow-ups.md"
    if dest.exists():
        return
    src = cfg.root / "templates" / "follow-ups.md"
    dest.write_text(src.read_text() if src.exists() else "# Follow-ups\n")
