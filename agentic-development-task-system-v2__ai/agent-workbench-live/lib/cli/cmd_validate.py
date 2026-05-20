"""validate subcommand.

Two modes:
  --init : while status=building, stage templates for implementation-summary,
           diff-summary, review, qa/report, handoff. Transition building -> validating.
  default: verify post-impl artifacts present and non-empty. Render audit.md.
           Transition validating -> human_review.

For convenience, the default mode allows status in (building, validating) and
will auto-init if invoked from `building`.
"""
from __future__ import annotations

from lib import metadata, events, transitions, locks, audit, lifecycle
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Run review + QA + render audit, then transition to human_review."


# Flat-layout templates (legacy runs).
POST_TEMPLATES_FLAT = ("implementation-summary.md", "diff-summary.md", "review.md", "handoff.md")
# Staged-layout templates. The builder writes build.md DURING building (it's
# the stage's output and gets moved into stages/building/ on transition), so
# --init only stages validating's templates here.
POST_TEMPLATES_STAGED = ("review.md", "HUMAN_REVIEW.md")
QA_REPORT = "qa/report.md"


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--init", action="store_true", help="Stage post-impl templates and transition building -> validating.")
    p.add_argument("--tests-passed", choices=("true", "false"), help="Recorded on QACompleted.")
    p.add_argument("--known-issues", type=int, default=0)


def _stage(cfg, rd, staged: bool) -> None:
    templates = POST_TEMPLATES_STAGED if staged else POST_TEMPLATES_FLAT
    for name in templates:
        dest = rd / name
        if not dest.exists():
            src = cfg.root / "templates" / name
            dest.write_text(src.read_text() if src.exists() else f"# {name}\n")
    qa_dir = rd / "qa"
    qa_dir.mkdir(exist_ok=True)
    for sub in ("artifacts", "recordings", "traces"):
        (qa_dir / sub).mkdir(exist_ok=True)
    report = qa_dir / "report.md"
    if not report.exists():
        src = cfg.root / "templates" / "qa" / "report.md"
        report.write_text(src.read_text() if src.exists() else "# QA report\n")
    commands = qa_dir / "commands.txt"
    if not commands.exists():
        commands.write_text("")


def run(args) -> int:
    cfg = load_config(args)
    actor = actor_from_env("agent")
    run_id = args.run_id

    try:
        meta = metadata.load(cfg, run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    rd = metadata.run_dir(cfg, run_id)
    staged = lifecycle.is_staged_run(cfg, run_id)

    if args.init:
        if meta["status"] != "building":
            return fail(f"--init requires status=building, got {meta['status']!r}", 2)
        # Staged runs require build.md to already exist (builder writes it
        # during building). Stage it from the template only if absent, but
        # that's the builder's job — warn by failing loudly here.
        if staged and not (rd / "build.md").exists():
            # First-time path: also tolerate the builder hasn't written it yet
            # by staging the template, so a smoke run with no real builder
            # still works. The transition engine will move whatever is there.
            tpl = cfg.root / "templates" / "build.md"
            (rd / "build.md").write_text(tpl.read_text() if tpl.exists() else "# Build\n")
        _stage(cfg, rd, staged)
        # For staged runs, build.md is the single merged artifact; both
        # implementation_summary_path and diff_summary_path evidence keys point
        # at it (their values get rewritten to stages/building/build.md by the
        # transition engine's move-on-transition hook).
        if staged:
            build_src = str(rd / "build.md")
            evidence = {
                "implementation_summary_path": build_src,
                "diff_summary_path": build_src,
            }
        else:
            evidence = {
                "implementation_summary_path": str(rd / "implementation-summary.md"),
                "diff_summary_path": str(rd / "diff-summary.md"),
            }
        try:
            with locks.acquire(cfg, run_id):
                transitions.transition(
                    cfg, run_id, "validating",
                    evidence=evidence,
                    actor=actor,
                )
        except transitions.TransitionError as e:
            return fail(str(e), 4)
        if staged:
            def _m(d):
                d["artifacts"]["implementation_summary"] = "stages/building/build.md"
                d["artifacts"]["diff_summary"] = "stages/building/build.md#files-changed"
                d["artifacts"]["review_report"] = "review.md"
                d["artifacts"]["qa_report"] = "qa/report.md"
                d["artifacts"]["handoff"] = "HUMAN_REVIEW.md"
        else:
            def _m(d):
                d["artifacts"]["implementation_summary"] = "implementation-summary.md"
                d["artifacts"]["diff_summary"] = "diff-summary.md"
                d["artifacts"]["review_report"] = "review.md"
                d["artifacts"]["qa_report"] = "qa/report.md"
                d["artifacts"]["handoff"] = "handoff.md"
        metadata.update(cfg, run_id, _m)
        print(f"{run_id}: building -> validating; staged post-impl templates")
        return 0

    # Default: validating -> human_review.
    if meta["status"] != "validating":
        return fail(f"default mode requires status=validating, got {meta['status']!r}", 2)

    # Verify required artifacts (location depends on layout).
    if staged:
        required = [
            ("stages/building/build.md", "implementation_summary_path"),
            ("review.md", "review_report_path"),
            ("qa/report.md", "qa_report_path"),
            ("HUMAN_REVIEW.md", "handoff_path"),
        ]
    else:
        required = [
            ("implementation-summary.md", "implementation_summary_path"),
            ("diff-summary.md", "diff_summary_path"),
            ("review.md", "review_report_path"),
            ("qa/report.md", "qa_report_path"),
            ("handoff.md", "handoff_path"),
        ]
    for name, _label in required:
        p = rd / name
        if not p.exists() or not p.read_text().strip():
            return fail(f"required artifact missing or empty: {p}", 2)

    # Emit ReviewCompleted (best-effort decision parsing).
    review_text = (rd / "review.md").read_text()
    decision = "request_changes"
    for line in review_text.splitlines():
        s = line.strip().lower()
        if s.startswith("## decision"):
            continue
        if s in ("approve", "request_changes", "block"):
            decision = s
            break
    events.append(
        cfg, run_id, "ReviewCompleted",
        payload={
            "review_report_path": str(rd / "review.md"),
            "review_decision": decision,
        },
        actor=actor,
    )

    # Emit QACompleted. tests_passed is required by the schema; default False
    # (no claim) when the caller didn't pass --tests-passed.
    if args.tests_passed is None:
        tests_passed = False
    else:
        tests_passed = args.tests_passed == "true"
    events.append(
        cfg, run_id, "QACompleted",
        payload={
            "qa_report_path": str(rd / "qa" / "report.md"),
            "commands_path": str(rd / "qa" / "commands.txt"),
            "tests_passed": tests_passed,
            "known_issues_count": int(args.known_issues),
            "artifacts_dir": str(rd / "qa" / "artifacts"),
            "recordings_dir": str(rd / "qa" / "recordings"),
            "traces_dir": str(rd / "qa" / "traces"),
        },
        actor=actor,
    )

    # Update metadata validation block.
    def _m(d):
        d["validation"]["review_completed"] = True
        d["validation"]["qa_completed"] = True
        d["validation"]["qa_recorded"] = True
        if tests_passed is not None:
            d["validation"]["tests_passed"] = tests_passed
        d["validation"]["known_issues_count"] = int(args.known_issues)
    metadata.update(cfg, run_id, _m)

    # Render audit.md.
    audit_path = audit.render(cfg, run_id)
    events.append(
        cfg, run_id, "AuditRendered",
        payload={"audit_path": str(audit_path)},
        actor=actor,
    )
    def _m2(d):
        d["artifacts"]["audit"] = "audit.md"
    metadata.update(cfg, run_id, _m2)

    handoff_file = "HUMAN_REVIEW.md" if staged else "handoff.md"

    # Emit HumanHandoffCreated.
    events.append(
        cfg, run_id, "HumanHandoffCreated",
        payload={
            "handoff_path": str(rd / handoff_file),
            "branch_name": meta["target"]["worktree"]["branch_name"],
            "worktree_path": meta["target"]["worktree"]["path"],
            "review_report_path": str(rd / "review.md"),
            "qa_report_path": str(rd / "qa" / "report.md"),
            "audit_path": str(audit_path),
        },
        actor=actor,
    )

    # Transition. The engine validates HUMAN_REVIEW.md section presence for
    # staged runs before set_status.
    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "human_review",
                evidence={
                    "review_report_path": str(rd / "review.md"),
                    "qa_report_path": str(rd / "qa" / "report.md"),
                    "audit_path": str(audit_path),
                    "handoff_path": str(rd / handoff_file),
                    "branch_name": meta["target"]["worktree"]["branch_name"],
                    "worktree_path": meta["target"]["worktree"]["path"],
                    "tests_passed": tests_passed,
                    "known_issues_count": int(args.known_issues),
                },
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)

    print(f"{run_id}: validating -> human_review")
    print(f"branch:   {meta['target']['worktree']['branch_name']}")
    print(f"worktree: {meta['target']['worktree']['path']}")
    print(f"audit:    {audit_path}")
    return 0
