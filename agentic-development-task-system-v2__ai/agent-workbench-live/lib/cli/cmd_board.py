"""board subcommand. Terminal-rendered Kanban over runs/.

One column per lifecycle state. Each card shows run_id, age since last update,
repo name, and branch. Terminal states (done, abandoned) are hidden unless
--all. Runs in human_review past the configured staleness threshold are
flagged.

The reader is `lib/metadata.load`; unreadable runs are skipped (board never
aborts because of one bad file).
"""
from __future__ import annotations

import datetime as dt

from lib import metadata
from lib.cli._common import load_config


HELP = "Show all runs grouped by lifecycle state."


# Canonical lifecycle order (matches docs/lifecycle.md, left to right).
COLUMN_ORDER = (
    "draft",
    "shaping",
    "planning",
    "ready",
    "building",
    "validating",
    "followups",
    "human_review",
    "done",
    "abandoned",
)

TERMINAL_STATES = ("done", "abandoned")

# Visual width of each column (chars). Wide enough for a typical run_id like
# `2026-05-21-better-worktree-name-template` (40 chars) without truncation.
COLUMN_WIDTH = 42
COLUMN_GUTTER = "  "


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


def format_age(seconds: float) -> str:
    """Largest unit ≥ 1 (m/h/d), integer. <1m shown as 0m."""
    s = max(0, int(seconds))
    minutes = s // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"
    return f"{hours // 24}d"


def _parse_iso(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts)


def _age_seconds(updated_at: str, now: dt.datetime) -> float:
    try:
        u = _parse_iso(updated_at)
    except Exception:
        return 0.0
    if u.tzinfo is None:
        u = u.replace(tzinfo=now.tzinfo)
    return (now - u).total_seconds()


def _stale_threshold_hours(cfg) -> int:
    board = (cfg.raw.get("board") or {})
    return int(board.get("stale_human_review_hours", 24))


def _truncate(s: str, width: int) -> str:
    if len(s) <= width:
        return s
    if width <= 1:
        return s[:width]
    return s[: width - 1] + "…"


def _pad(s: str, width: int) -> str:
    s = _truncate(s, width)
    return s + " " * (width - len(s))


def build_columns(
    runs: list[dict],
    *,
    show_all: bool,
    only_status: str | None,
    stale_hours: int,
    now: dt.datetime,
) -> dict[str, list[dict]]:
    """Group runs by status. Returns ordered dict-of-list keyed by COLUMN_ORDER."""
    cols: dict[str, list[dict]] = {s: [] for s in COLUMN_ORDER}
    for m in runs:
        status = m.get("status")
        if status not in cols:
            continue
        if only_status and status != only_status:
            continue
        if not show_all and not only_status and status in TERMINAL_STATES:
            continue
        age_s = _age_seconds(m.get("updated_at", ""), now)
        is_stale = (
            status == "human_review"
            and age_s >= stale_hours * 3600
        )
        cols[status].append({
            "run_id": m["run_id"],
            "age_seconds": age_s,
            "repo_name": (m.get("target") or {}).get("repo", {}).get("name", ""),
            "branch": (m.get("target") or {}).get("worktree", {}).get("branch_name", ""),
            "is_stale": is_stale,
        })
    # Sort cards within a column oldest-update-first (largest age first) so
    # the things that have sat the longest float to the top.
    for s in cols:
        cols[s].sort(key=lambda c: -c["age_seconds"])
    return cols


def _card_lines(card: dict) -> list[str]:
    marker = "! " if card["is_stale"] else ""
    return [
        f"{marker}{card['run_id']}",
        f"{format_age(card['age_seconds'])} · {card['repo_name']}",
        card["branch"],
    ]


def _render(cols: dict[str, list[dict]]) -> str:
    visible = [(s, cards) for s, cards in cols.items() if cards]
    if not visible:
        return ""

    # Header row.
    out: list[str] = []
    header = COLUMN_GUTTER.join(_pad(s, COLUMN_WIDTH) for s, _ in visible)
    rule = COLUMN_GUTTER.join("-" * COLUMN_WIDTH for _ in visible)
    counts = COLUMN_GUTTER.join(
        _pad(f"({len(cards)})", COLUMN_WIDTH) for _, cards in visible
    )
    out.append(header.rstrip())
    out.append(counts.rstrip())
    out.append(rule)

    # Card rows: stack cards vertically within each column, aligned by row.
    max_cards = max(len(cards) for _, cards in visible)
    for i in range(max_cards):
        # 3 card lines + 1 blank.
        for line_idx in range(3):
            row_pieces = []
            for _, cards in visible:
                if i < len(cards):
                    line = _card_lines(cards[i])[line_idx]
                else:
                    line = ""
                row_pieces.append(_pad(line, COLUMN_WIDTH))
            out.append(COLUMN_GUTTER.join(row_pieces).rstrip())
        out.append("")  # blank separator between cards
    return "\n".join(out).rstrip() + "\n"


def _stale_footer(cols: dict[str, list[dict]]) -> str:
    stale = [c for c in cols.get("human_review", []) if c["is_stale"]]
    if not stale:
        return ""
    lines = ["Stale human_review:"]
    for c in stale:
        lines.append(f"  ! {c['run_id']}  ({format_age(c['age_seconds'])})")
    return "\n".join(lines) + "\n"


def run(args) -> int:
    cfg = load_config(args)
    now = dt.datetime.now().astimezone()
    stale_hours = _stale_threshold_hours(cfg)

    loaded: list[dict] = []
    for rid in metadata.list_runs(cfg):
        try:
            loaded.append(metadata.load(cfg, rid))
        except Exception:
            # Board should never abort because one run's metadata is unreadable
            # (malformed YAML, missing fields, etc). Skip and continue.
            continue

    if not loaded:
        print("(no runs)")
        return 0

    cols = build_columns(
        loaded,
        show_all=bool(args.all),
        only_status=args.status,
        stale_hours=stale_hours,
        now=now,
    )

    rendered = _render(cols)
    if not rendered:
        print("(no runs)")
        return 0

    print(rendered, end="")
    footer = _stale_footer(cols)
    if footer:
        print()
        print(footer, end="")
    return 0
