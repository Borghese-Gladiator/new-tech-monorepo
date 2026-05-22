"""Pure-function readers that produce one RunSnapshot per run on disk.

No Textual import here — this module is the on-disk reader, callable from
tests without a TTY. The snapshot is the input to both the live TUI and the
fallback `--static` text render.

Source of truth = the filesystem. Each call re-reads metadata.yaml + a
configurable tail of events.jsonl. No caching between calls; staleness is
the failure mode we refuse to ship.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import pathlib
from typing import Any

from lib import lifecycle, metadata
from lib.config import Config


# Lifecycle states in canonical left-to-right column order.
COLUMN_ORDER: tuple[str, ...] = (
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

TERMINAL_STATES: tuple[str, ...] = ("done", "abandoned")


@dataclasses.dataclass(frozen=True)
class EventSummary:
    """One line of recent activity rendered on a card."""
    at: str             # ISO timestamp string from the event
    age_seconds: float  # seconds between event.at and snapshot.now
    type: str           # event_type (e.g. "ArtifactWritten")
    detail: str         # short human-readable detail (e.g. "review.md")


@dataclasses.dataclass(frozen=True)
class RunSnapshot:
    """Everything the board needs to render one card. Frozen, value-typed."""
    run_id: str
    status: str
    repo_name: str
    branch_name: str
    worktree_name: str
    run_dir: str
    worktree_path: str
    created_at: str
    updated_at: str

    # Derived ages (seconds).
    age_seconds: float                    # since updated_at
    total_age_seconds: float              # since created_at
    time_in_stage_seconds: float | None   # since last TransitionApplied; None if unknown

    # Stage-aware progress.
    build_iterations: int | None
    build_max_iterations: int | None
    build_exit_reason: str | None
    build_md_exists: bool

    # Validation flags.
    review_completed: bool
    qa_completed: bool
    tests_passed: bool | None
    known_issues_count: int

    # Followups stage signal.
    followups_entry_count: int | None

    # Health flags.
    is_stale_human_review: bool
    builder_gave_up: bool        # build.exit_reason == "max_iterations"
    failing_tests: bool          # validation.tests_passed == False
    has_known_issues: bool       # validation.known_issues_count > 0
    has_recent_error: bool       # ErrorRecorded since last TransitionApplied
    bounce_count: int            # number of BounceRequested events
    recent_bounce_reason: str | None

    # Live-tail recent events (newest first).
    recent_events: tuple[EventSummary, ...]


def _parse_iso(ts: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(ts)
    except Exception:
        return None


def _seconds_between(ts: str, now: dt.datetime) -> float:
    parsed = _parse_iso(ts)
    if parsed is None:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=now.tzinfo)
    return max(0.0, (now - parsed).total_seconds())


def _short_actor(actor: dict | None) -> str:
    if not isinstance(actor, dict):
        return ""
    return str(actor.get("name") or "")


def _event_detail(ev: dict) -> str:
    """One-line summary of an event. Detail varies by type."""
    et = ev.get("type", "")
    payload = ev.get("payload") or {}

    if et == "ArtifactWritten":
        key = payload.get("artifact_key") or ""
        # Trim the path to its basename for the card.
        raw = payload.get("path") or ""
        base = pathlib.Path(raw).name if raw else ""
        return f"{key}={base}" if key and base else (key or base or "")
    if et == "TransitionApplied":
        return f"{ev.get('from','?')} -> {ev.get('to','?')}"
    if et == "CommandRun":
        cmd = payload.get("command") or ""
        # Keep cards narrow: clamp to the binary name + first arg.
        return cmd.split("\n", 1)[0][:48]
    if et == "BounceRequested":
        return str(payload.get("bounce_reason") or "")[:48]
    if et == "ErrorRecorded":
        return f"{payload.get('error_kind','')}: {payload.get('message','')}"[:48]
    if et == "ReviewCompleted":
        return str(payload.get("review_decision") or "")
    if et == "QACompleted":
        passed = payload.get("tests_passed")
        return "tests passed" if passed else "tests failed"
    if et == "FollowupsRecorded":
        n = payload.get("entry_count")
        return f"{n} entries" if n is not None else ""
    if et == "DocClaimsVerified":
        unverified = payload.get("unverified") or []
        return f"{len(unverified)} unverified" if unverified else "ok"
    if et == "ScopeCreepChecked":
        creep = payload.get("creep") or []
        return f"{len(creep)} creep" if creep else "clean"
    return ""


def _iter_events(events_path: pathlib.Path):
    """Yield each event as a dict. Skips empty / malformed lines silently."""
    if not events_path.exists():
        return
    try:
        text = events_path.read_text()
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def load_run_snapshot(
    cfg: Config,
    run_id: str,
    *,
    now: dt.datetime,
    stale_human_review_seconds: int,
    recent_event_count: int = 3,
) -> RunSnapshot | None:
    """Read one run off disk and return a frozen RunSnapshot.

    Returns None if metadata is missing or malformed — the board renders
    everything else; one bad run never breaks the view.
    """
    try:
        meta = metadata.load(cfg, run_id)
    except Exception:
        return None

    status = meta.get("status", "")
    target = meta.get("target") or {}
    repo = target.get("repo") or {}
    worktree = target.get("worktree") or {}
    validation = meta.get("validation") or {}
    build = meta.get("build") or {}

    created_at = meta.get("created_at", "")
    updated_at = meta.get("updated_at", "")

    rd = metadata.run_dir(cfg, run_id)
    events_path = rd / "events.jsonl"

    # Walk events to compute time-in-stage, recent activity, bounce count, error flag.
    events = list(_iter_events(events_path))
    time_in_stage_s: float | None = None
    for ev in reversed(events):
        if ev.get("type") == "TransitionApplied" and ev.get("to") == status:
            time_in_stage_s = _seconds_between(ev.get("at", ""), now)
            break

    bounce_count = sum(1 for ev in events if ev.get("type") == "BounceRequested")
    recent_bounce_reason: str | None = None
    for ev in reversed(events):
        if ev.get("type") == "BounceRequested":
            recent_bounce_reason = str((ev.get("payload") or {}).get("bounce_reason") or "") or None
            break

    # has_recent_error = any ErrorRecorded after the last TransitionApplied.
    has_recent_error = False
    for ev in reversed(events):
        et = ev.get("type")
        if et == "TransitionApplied":
            break
        if et == "ErrorRecorded":
            has_recent_error = True
            break

    # Build the last-N event list (newest first).
    recent: list[EventSummary] = []
    for ev in reversed(events):
        if len(recent) >= recent_event_count:
            break
        et = ev.get("type", "")
        if not et:
            continue
        at = ev.get("at", "")
        recent.append(EventSummary(
            at=at,
            age_seconds=_seconds_between(at, now),
            type=et,
            detail=_event_detail(ev),
        ))

    # Stage-aware: is the build.md present in stages/4_building/?
    build_md_exists = False
    try:
        build_md_path = lifecycle.stage_dir(cfg, run_id, "building") / "build.md"
        build_md_exists = build_md_path.exists()
    except Exception:
        # If the run is flat-layout or stage_dir errors for any reason,
        # check the flat location too.
        build_md_exists = (rd / "build.md").exists()

    # Followups entry count: prefer the latest FollowupsRecorded payload over
    # parsing the file (the event is the source of truth post-validate).
    followups_entry_count: int | None = None
    for ev in reversed(events):
        if ev.get("type") == "FollowupsRecorded":
            payload = ev.get("payload") or {}
            try:
                followups_entry_count = int(payload.get("entry_count"))
            except (TypeError, ValueError):
                followups_entry_count = None
            break

    # Derived flags.
    age_s = _seconds_between(updated_at, now)
    total_age_s = _seconds_between(created_at, now)
    is_stale = (status == "human_review" and age_s >= stale_human_review_seconds)
    builder_gave_up = (build.get("exit_reason") == "max_iterations")
    tests_passed = validation.get("tests_passed")  # may be None
    failing_tests = (tests_passed is False)
    known_issues_count = int(validation.get("known_issues_count") or 0)
    has_known_issues = known_issues_count > 0

    return RunSnapshot(
        run_id=run_id,
        status=status,
        repo_name=str(repo.get("name") or ""),
        branch_name=str(worktree.get("branch_name") or ""),
        worktree_name=str(worktree.get("name") or ""),
        run_dir=str(rd),
        worktree_path=str(worktree.get("path") or ""),
        created_at=created_at,
        updated_at=updated_at,
        age_seconds=age_s,
        total_age_seconds=total_age_s,
        time_in_stage_seconds=time_in_stage_s,
        build_iterations=_maybe_int(build.get("iterations")),
        build_max_iterations=_maybe_int(build.get("max_iterations")),
        build_exit_reason=_maybe_str(build.get("exit_reason")),
        build_md_exists=build_md_exists,
        review_completed=bool(validation.get("review_completed")),
        qa_completed=bool(validation.get("qa_completed")),
        tests_passed=tests_passed if isinstance(tests_passed, bool) else None,
        known_issues_count=known_issues_count,
        followups_entry_count=followups_entry_count,
        is_stale_human_review=is_stale,
        builder_gave_up=builder_gave_up,
        failing_tests=failing_tests,
        has_known_issues=has_known_issues,
        has_recent_error=has_recent_error,
        bounce_count=bounce_count,
        recent_bounce_reason=recent_bounce_reason,
        recent_events=tuple(recent),
    )


def _maybe_int(v: Any) -> int | None:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _maybe_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v)
    return s or None


def stale_threshold_seconds(cfg: Config) -> int:
    board = (cfg.raw.get("board") or {})
    hours = int(board.get("stale_human_review_hours", 24))
    return hours * 3600


def is_loud(run: RunSnapshot) -> bool:
    """Cards that should get a red bar / loud column marker."""
    return (
        run.is_stale_human_review
        or run.builder_gave_up
        or run.failing_tests
        or run.has_known_issues
        or run.has_recent_error
    )
