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
    from lib.board.source import is_loud

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

    # Per card: a short stack of lines.
    if compact:
        lines_per_card = 1
    else:
        lines_per_card = 4  # title, age/repo, branch, blank
    max_cards = max(c.count for c in visible) if visible else 0

    for i in range(max_cards):
        for line_idx in range(lines_per_card):
            row_pieces = []
            for c in visible:
                if i < c.count:
                    run = c.runs[i]
                    line = _static_card_line(run, line_idx, compact=compact)
                else:
                    line = ""
                row_pieces.append(pad(line, column_width))
            print(gutter.join(row_pieces).rstrip())

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
    from lib.board.snapshot import format_age
    from lib.board.source import is_loud

    marker = "! " if is_loud(run) else ""
    if compact:
        bits = [marker + run.run_id, format_age(run.age_seconds)]
        if run.repo_name:
            bits.append(run.repo_name)
        return " · ".join(bits)

    if line_idx == 0:
        return f"{marker}{run.run_id}"
    if line_idx == 1:
        return f"{format_age(run.age_seconds)} · {run.repo_name}"
    if line_idx == 2:
        return run.branch_name
    return ""


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
