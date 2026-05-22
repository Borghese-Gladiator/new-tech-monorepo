"""Textual app rendering the live Agent Workbench board.

Imports Textual + watchdog (the only third-party deps in the workbench).
Module-level imports are intentional — `cmd_board` imports this module
lazily so the rest of the CLI stays stdlib-only.

Refresh model:
  - A watchdog Observer fires on every filesystem change under runs/.
    Each event posts a Textual message that triggers a snapshot rebuild.
  - A 1Hz fallback timer rebuilds the snapshot regardless. This keeps the
    age tickers moving even when nothing changed and rescues us if a
    filesystem doesn't deliver inotify-equivalent events.

The app does not maintain a stateful in-memory model of runs; every refresh
re-reads disk via lib/board/snapshot.build. Cheap and correct trumps subtle.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import pathlib
from typing import Iterable

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Static
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lib.board import snapshot as snapshot_mod
from lib.board.snapshot import format_age
from lib.board.source import COLUMN_ORDER, RunSnapshot, is_loud
from lib.config import Config


# Card width / column width. Picked to fit a typical run_id (40 chars) +
# small padding without horizontal wrap inside the card.
_CARD_WIDTH = 42


# ---------- Rich-based card rendering ----------

def _card_text(run: RunSnapshot, *, compact: bool) -> Text:
    """Render one card as a Rich Text object.

    Status-aware: a draft card shows almost nothing; a building card
    prioritizes iteration progress; a validating card prioritizes flags.
    """
    loud = is_loud(run)
    text = Text()

    # Title line — run_id, status badge, optional scope kind, live marker.
    marker = "! " if loud else ""
    title_style = "bold red" if loud else "bold"
    text.append(f"{marker}{run.run_id}", style=title_style)
    text.append(f"  [{run.status}]", style="dim")
    if run.scope_kind:
        text.append(f"  {run.scope_kind}", style="dim")
    if run.is_live:
        text.append("  ● live", style="green")
    text.append("\n")

    if compact:
        bits = []
        bits.append(format_age(run.age_seconds))
        bits.append(run.repo_name)
        if run.is_stale_human_review:
            bits.append("stale")
        if run.failing_tests:
            bits.append("tests-fail")
        if run.builder_gave_up:
            bits.append("max-iter")
        if run.worktree_missing:
            bits.append("wt-missing")
        text.append(" · ".join(b for b in bits if b))
        return text

    # Age / repo line.
    text.append(f"{format_age(run.age_seconds)} since update", style="dim")
    if run.repo_name:
        text.append(f" · {run.repo_name}", style="dim")
    text.append("\n")

    # Show repo_path_tail when it adds info beyond repo_name (basename
    # collisions across two repos called `repo`, for example).
    if run.repo_path_tail and run.repo_path_tail != run.repo_name:
        text.append(f"repo {run.repo_path_tail}\n", style="dim")

    if run.branch_name:
        text.append(f"branch {run.branch_name}\n", style="dim")

    # Stage-aware body.
    body_lines = list(_status_body(run))
    for ln in body_lines:
        text.append(ln + "\n")

    if run.worktree_missing:
        text.append("! worktree missing\n", style="yellow")

    # Last events tail.
    if run.recent_events:
        text.append("\nevents:\n", style="dim")
        for ev in run.recent_events:
            line = f"  {ev.type}"
            if ev.detail:
                line += f" {ev.detail}"
            line += f" · {format_age(ev.age_seconds)}\n"
            text.append(line, style="dim")

    # Audit links.
    if run.run_dir:
        text.append(f"\n{run.run_dir}\n", style="dim italic")
    if run.worktree_path:
        text.append(f"{run.worktree_path}\n", style="dim italic")

    return text


def _status_body(run: RunSnapshot) -> Iterable[str]:
    """Yield status-specific body lines (not including title/age/branch)."""
    if run.status == "draft":
        return
    if run.status == "building":
        cur = run.build_iterations
        mx = run.build_max_iterations
        if cur is not None and mx:
            bar = _progress_bar(cur, mx, width=10)
            yield f"build {cur}/{mx} {bar}"
        if run.avg_iteration_seconds is not None:
            yield f"avg {format_age(run.avg_iteration_seconds)}/iter"
        if run.build_md_exists:
            yield "build.md present"
        if run.builder_gave_up:
            yield "! builder gave up (max_iterations)"
        if run.bounced_from:
            age = (
                format_age(run.bounced_at_age_seconds)
                if run.bounced_at_age_seconds is not None else "?"
            )
            yield f"↩ bounced from {run.bounced_from} · {age} ago"
        if run.recent_bounce_reason and not run.bounced_from:
            # Surface the most recent reason even when the latest transition
            # wasn't a bounce (e.g., a reviewer asked for changes earlier).
            yield f"bounced: {run.recent_bounce_reason}"
        for line in _diff_lines(run):
            yield line
        return
    if run.status == "validating":
        ck = "tests"
        tp = run.tests_passed
        mark = "?" if tp is None else ("✓" if tp else "✗")
        head = f"{ck} {mark}"
        if run.tests_recorded_age_seconds is not None:
            head += f" · {format_age(run.tests_recorded_age_seconds)} ago"
        yield (
            f"{head}  rev {'✓' if run.review_completed else '·'}"
            f"  qa {'✓' if run.qa_completed else '·'}"
        )
        if run.ac_total is not None:
            mark = ""
            if run.ac_covered is not None and run.ac_total > 0 and run.ac_covered < run.ac_total:
                mark = " !"
            yield f"{run.ac_covered}/{run.ac_total} ACs covered{mark}"
        elif run.ac_table_missing:
            yield "AC table missing"
        if run.has_known_issues:
            yield f"known_issues: {run.known_issues_count}"
        for line in _diff_lines(run):
            yield line
        return
    if run.status == "followups":
        if run.followups_entry_count is not None:
            yield f"follow-ups: {run.followups_entry_count}"
        for line in _followups_breakdown(run):
            yield line
        return
    if run.status == "human_review":
        if run.is_stale_human_review:
            yield f"! stale {format_age(run.age_seconds)}"
        if run.bounce_count:
            yield f"bounces: {run.bounce_count}"
        if run.followups_entry_count is not None:
            yield f"follow-ups: {run.followups_entry_count}"
        for line in _followups_breakdown(run):
            yield line
        return
    if run.status == "done":
        if run.accepted_by or run.completed_at:
            who = run.accepted_by or "?"
            when = _hhmm(run.completed_at) if run.completed_at else "?"
            yield f"accepted_by {who} · {when}"
        return
    if run.status == "abandoned":
        if run.abandoned_reason:
            yield f"abandoned: {run.abandoned_reason}"
        return
    # Other states (shaping, planning, ready) currently add no extra
    # lines; identity + age suffice.
    return


def _diff_lines(run: RunSnapshot) -> Iterable[str]:
    if run.diff_files is None:
        return
    if not run.diff_files and not run.diff_added and not run.diff_removed:
        return
    yield (
        f"+{run.diff_added or 0}/-{run.diff_removed or 0} "
        f"across {run.diff_files} file{'s' if run.diff_files != 1 else ''}"
    )


def _followups_breakdown(run: RunSnapshot) -> Iterable[str]:
    if not run.followups_categories:
        return
    bits = [f"{count} {cat}" for cat, count in run.followups_categories]
    yield "  · " + " · ".join(bits)


def _hhmm(ts: str) -> str:
    """Format an ISO timestamp as HH:MM (local). Best-effort."""
    try:
        return dt.datetime.fromisoformat(ts).strftime("%H:%M")
    except Exception:
        return ts[11:16] if len(ts) >= 16 else ts


def _progress_bar(cur: int, mx: int, *, width: int = 10) -> str:
    if mx <= 0:
        return ""
    filled = max(0, min(width, int(round(width * cur / mx))))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


# ---------- Textual widgets ----------

class RunCard(Static):
    """One card. Wraps a RunSnapshot in a fixed-width Static."""

    DEFAULT_CSS = """
    RunCard {
        width: 42;
        padding: 0 1;
        margin: 0 0 1 0;
        border: tall $surface;
    }
    RunCard.-loud {
        border: tall red;
    }
    """

    def __init__(self, run: RunSnapshot, *, compact: bool):
        super().__init__(_card_text(run, compact=compact))
        if is_loud(run):
            self.add_class("-loud")


class StatusColumn(Vertical):
    """One Kanban column: header strip + scrollable card stack."""

    DEFAULT_CSS = """
    StatusColumn {
        width: 44;
        height: 100%;
        padding: 0 1;
    }
    StatusColumn > .column-header {
        height: 2;
        content-align: left middle;
    }
    StatusColumn > ScrollableContainer {
        height: 1fr;
    }
    """

    def __init__(self, status: str):
        super().__init__()
        self.status = status
        self._header = Static("", classes="column-header")
        self._body = ScrollableContainer()

    def compose(self) -> ComposeResult:
        yield self._header
        yield self._body

    def update_column(self, runs: tuple[RunSnapshot, ...], *, compact: bool) -> None:
        loud = any(is_loud(r) for r in runs)
        marker = " !" if loud else ""
        header = Text()
        header.append(self.status, style="bold")
        header.append(f"  ({len(runs)}){marker}", style="dim")
        self._header.update(header)

        # Replace body children. Textual's remove() is async-friendly via
        # `await` but for a re-render we want a clean swap; use the sync
        # mount-by-rebuild pattern.
        self._body.remove_children()
        for r in runs:
            self._body.mount(RunCard(r, compact=compact))


# ---------- Watchdog -> Textual bridge ----------

class RunsChanged(Message):
    """Posted by the watchdog thread when something under runs/ changed."""


class _Handler(FileSystemEventHandler):
    def __init__(self, app: "AgentBoardApp"):
        self._app = app

    def on_any_event(self, event):  # noqa: D401
        # Filter noise: ignore .tmp atomic rename suffixes (the metadata
        # writer renames .tmp -> .yaml, which fires both events; we only
        # care about the final one).
        path = getattr(event, "src_path", "") or ""
        if path.endswith(".tmp"):
            return
        # Post a Textual message back to the app's thread.
        try:
            self._app.call_from_thread(self._app.post_message, RunsChanged())
        except Exception:
            # App may be shutting down; ignore.
            pass


# ---------- The app ----------

@dataclasses.dataclass(frozen=True)
class BoardOptions:
    show_all: bool = False
    only_status: str | None = None
    compact: bool = False


class AgentBoardApp(App):
    """Full-screen TUI rendering the Agent Workbench board.

    The board is read-only beyond `q`. Re-render is driven by:
      - watchdog events on runs/
      - a 1Hz fallback timer (also drives the age ticker)
    """

    CSS = """
    Screen {
        layout: vertical;
    }
    #columns {
        layout: horizontal;
        height: 1fr;
        overflow-x: auto;
    }
    """

    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, cfg: Config, opts: BoardOptions):
        super().__init__()
        self._cfg = cfg
        self._opts = opts
        self._observer: Observer | None = None
        self._columns: dict[str, StatusColumn] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="columns"):
            for status in COLUMN_ORDER:
                col = StatusColumn(status)
                self._columns[status] = col
                yield col
        yield Footer()

    def on_mount(self) -> None:
        # Initial render.
        self._refresh()
        # 1 Hz fallback timer for liveness + age tickers.
        self.set_interval(1.0, self._refresh)
        # Watchdog observer for low-latency response to file changes.
        runs_path = self._cfg.runs_path
        runs_path.mkdir(parents=True, exist_ok=True)
        obs = Observer()
        obs.schedule(_Handler(self), str(runs_path), recursive=True)
        obs.daemon = True
        obs.start()
        self._observer = obs

    def on_unmount(self) -> None:
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=1.0)
            except Exception:
                pass

    def on_runs_changed(self, _: RunsChanged) -> None:
        self._refresh()

    def _refresh(self) -> None:
        snap = snapshot_mod.build(
            self._cfg,
            show_all=self._opts.show_all,
            only_status=self._opts.only_status,
        )

        # Visible set: when filtering by status, only that one column shows;
        # otherwise show every canonical column whose count > 0, plus any
        # column the user asked about.
        visible_statuses = {c.status for c in snap.visible_columns()}
        if self._opts.only_status:
            visible_statuses = {self._opts.only_status}

        for status, col in self._columns.items():
            column = next((c for c in snap.columns if c.status == status), None)
            runs = column.runs if column else ()
            col.update_column(runs, compact=self._opts.compact)
            col.display = (status in visible_statuses) or bool(runs)

        # Update the header subtitle with timestamp + total runs.
        self.title = "Agent Workbench"
        self.sub_title = (
            f"{snap.total_runs} run(s) · "
            f"watch + 1Hz · {snap.now.strftime('%H:%M:%S')}"
        )


def run(cfg: Config, opts: BoardOptions) -> int:
    AgentBoardApp(cfg, opts).run()
    return 0
