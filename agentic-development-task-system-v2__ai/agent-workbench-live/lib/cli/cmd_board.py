"""board subcommand. Live Textual TUI over runs/.

The default behaviour is the live board (`lib.board.app.AgentBoardApp`),
which auto-refreshes via watchdog + a 1Hz fallback. This requires the
optional `textual` + `watchdog` dependencies. Install with:

    pip install -r requirements-board.txt

Run `agent-workbench board --static` for the stdlib-only one-shot text
render. CI and headless callers should use that path.
"""
from __future__ import annotations

import datetime as dt

from lib.cli._common import fail, load_config


HELP = "Live task board: Kanban over runs/, refreshes on every file change."


def register(p) -> None:
    p.add_argument(
        "--all",
        action="store_true",
        help="Include terminal states (done, abandoned).",
    )
    p.add_argument(
        "--status",
        help="Show only this status column.",
    )
    p.add_argument(
        "--compact",
        action="store_true",
        help="One-line cards. Useful in narrow terminals.",
    )
    p.add_argument(
        "--static",
        action="store_true",
        help="Print a one-shot stdlib-only text render and exit (no TUI).",
    )


def _static_render(cfg, *, show_all: bool, only_status: str | None, compact: bool) -> int:
    """Stdlib-only one-shot text render. No textual import."""
    from lib.board import snapshot as snapshot_mod
    from lib.board.snapshot import format_age

    snap = snapshot_mod.build(cfg, show_all=show_all, only_status=only_status)
    visible = snap.visible_columns()
    if not visible:
        print("(no runs)")
        return 0

    column_width = 42
    gutter = "  "

    def pad(s: str, w: int) -> str:
        s = s if len(s) <= w else (s[: w - 1] + "…")
        return s + " " * (w - len(s))

    # Headers + counts + rule.
    header = gutter.join(pad(c.status, column_width) for c in visible)
    counts = gutter.join(
        pad(f"({c.count}){' !' if c.has_loud_card else ''}", column_width)
        for c in visible
    )
    rule = gutter.join("-" * column_width for _ in visible)
    print(header.rstrip())
    print(counts.rstrip())
    print(rule)

    # Per card: a stack of lines. In compact mode it's one. Otherwise the
    # static dump precomputes a status-aware stack and pads every column
    # to the tallest stack.
    if compact:
        column_lines: list[list[list[str]]] = [
            [[_static_card_line(r, 0, compact=True)] for r in c.runs]
            for c in visible
        ]
    else:
        column_lines = [
            [_static_card_stack(r) for r in c.runs]
            for c in visible
        ]

    max_cards = max(c.count for c in visible) if visible else 0
    for i in range(max_cards):
        # Each card across columns may have a different stack height;
        # render the tallest stack here, padding shorter cards with blanks.
        per_column_card_lines: list[list[str]] = []
        for col_idx in range(len(visible)):
            cards = column_lines[col_idx]
            per_column_card_lines.append(cards[i] if i < len(cards) else [])
        stack_height = max((len(lines) for lines in per_column_card_lines), default=0)
        for line_idx in range(stack_height):
            row_pieces = []
            for lines in per_column_card_lines:
                line = lines[line_idx] if line_idx < len(lines) else ""
                row_pieces.append(pad(line, column_width))
            print(gutter.join(row_pieces).rstrip())
        # Blank separator between cards.
        if i + 1 < max_cards:
            print(gutter.join(pad("", column_width) for _ in visible).rstrip())

    # Stale human_review footer (preserves the v0 contract that the
    # static dump still ends with a stale-list footer).
    stale = [
        r for c in visible
        for r in c.runs
        if r.is_stale_human_review
    ]
    if stale:
        print()
        print("Stale human_review:")
        for r in stale:
            print(f"  ! {r.run_id}  ({format_age(r.age_seconds)})")
    return 0


def _static_card_line(run, line_idx: int, *, compact: bool) -> str:
    """Compact one-liner (used in --compact mode only)."""
    from lib.board.snapshot import format_age
    from lib.board.source import is_loud

    marker = "! " if is_loud(run) else ""
    bits = [marker + run.run_id, format_age(run.age_seconds)]
    if run.repo_name:
        bits.append(run.repo_name)
    if run.is_live:
        bits.append("live")
    if run.worktree_missing:
        bits.append("wt-missing")
    if run.failing_tests:
        bits.append("tests-fail")
    if run.builder_gave_up:
        bits.append("max-iter")
    return " · ".join(bits)


def _static_card_stack(run) -> list[str]:
    """Status-aware stack of lines for the non-compact static renderer."""
    from lib.board.snapshot import format_age
    from lib.board.source import is_loud

    marker = "! " if is_loud(run) else ""
    lines: list[str] = []

    head = f"{marker}{run.run_id}  [{run.status}]"
    if run.scope_kind:
        head += f"  {run.scope_kind}"
    if run.is_live:
        head += "  live"
    lines.append(head)

    lines.append(f"{format_age(run.age_seconds)} · {run.repo_name}")
    if run.repo_path_tail and run.repo_path_tail != run.repo_name:
        lines.append(f"  {run.repo_path_tail}")
    if run.branch_name:
        lines.append(run.branch_name)

    # Status-aware data lines.
    if run.status == "building":
        if run.build_iterations is not None and run.build_max_iterations:
            lines.append(f"build {run.build_iterations}/{run.build_max_iterations}")
        if run.avg_iteration_seconds is not None:
            lines.append(f"avg {format_age(run.avg_iteration_seconds)}/iter")
        if run.bounced_from:
            age = (
                format_age(run.bounced_at_age_seconds)
                if run.bounced_at_age_seconds is not None else "?"
            )
            lines.append(f"bounced from {run.bounced_from} · {age} ago")
        if run.diff_files:
            lines.append(
                f"+{run.diff_added or 0}/-{run.diff_removed or 0} "
                f"across {run.diff_files} files"
            )
    elif run.status == "validating":
        tp = run.tests_passed
        mark = "?" if tp is None else ("✓" if tp else "✗")
        head = f"tests {mark}"
        if run.tests_recorded_age_seconds is not None:
            head += f" · {format_age(run.tests_recorded_age_seconds)} ago"
        lines.append(
            f"{head}  rev {'✓' if run.review_completed else '·'}"
            f"  qa {'✓' if run.qa_completed else '·'}"
        )
        if run.ac_total is not None:
            tag = " !" if (
                run.ac_covered is not None
                and run.ac_total > 0
                and run.ac_covered < run.ac_total
            ) else ""
            lines.append(f"{run.ac_covered}/{run.ac_total} ACs covered{tag}")
        elif run.ac_table_missing:
            lines.append("AC table missing")
        if run.has_known_issues:
            lines.append(f"known_issues: {run.known_issues_count}")
        if run.diff_files:
            lines.append(
                f"+{run.diff_added or 0}/-{run.diff_removed or 0} "
                f"across {run.diff_files} files"
            )
    elif run.status == "followups":
        if run.followups_entry_count is not None:
            lines.append(f"follow-ups: {run.followups_entry_count}")
        for cat, count in run.followups_categories:
            lines.append(f"  {count} {cat}")
    elif run.status == "human_review":
        if run.is_stale_human_review:
            lines.append(f"! stale {format_age(run.age_seconds)}")
        if run.bounce_count:
            lines.append(f"bounces: {run.bounce_count}")
        if run.followups_entry_count is not None:
            lines.append(f"follow-ups: {run.followups_entry_count}")
    elif run.status == "done":
        if run.accepted_by or run.completed_at:
            who = run.accepted_by or "?"
            when = (run.completed_at or "")[11:16]
            lines.append(f"accepted_by {who} · {when}")
    elif run.status == "abandoned":
        if run.abandoned_reason:
            lines.append(f"abandoned: {run.abandoned_reason}")

    if run.worktree_missing:
        lines.append("! worktree missing")
    return lines


def run(args) -> int:
    cfg = load_config(args)

    if args.static:
        return _static_render(
            cfg,
            show_all=bool(args.all),
            only_status=args.status,
            compact=bool(args.compact),
        )

    # Live TUI. Lazy-import: keep the rest of the CLI stdlib-only.
    try:
        from lib.board.app import AgentBoardApp, BoardOptions
    except ImportError as e:
        return fail(
            "live board needs `textual` and `watchdog`. install with:\n"
            "    pip install -r requirements-board.txt\n"
            f"(import failed: {e})\n"
            "Use `agent-workbench board --static` for the stdlib-only fallback."
        )

    opts = BoardOptions(
        show_all=bool(args.all),
        only_status=args.status,
        compact=bool(args.compact),
    )
    AgentBoardApp(cfg, opts).run()
    return 0
