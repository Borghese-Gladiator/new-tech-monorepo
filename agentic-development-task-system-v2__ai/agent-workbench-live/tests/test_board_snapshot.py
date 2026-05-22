"""Unit tests for lib/board/snapshot.py and lib/board/source.py.

Seed fake runs/ trees and assert derived fields, health flags, recent events,
and column grouping. No TTY required.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import textwrap
import unittest

from tests._helpers import make_tmp_workbench, cleanup, reset_caches


def _iso(ts: dt.datetime) -> str:
    return ts.astimezone().replace(microsecond=0).isoformat()


def seed_run(
    root: pathlib.Path,
    run_id: str,
    *,
    status: str,
    repo_name: str = "repo",
    branch: str = "agent/branch",
    worktree_name: str = "wt",
    created_at: dt.datetime | None = None,
    updated_at: dt.datetime | None = None,
    review_completed: bool = False,
    qa_completed: bool = False,
    tests_passed: bool | None = None,
    known_issues_count: int = 0,
    build_iterations: int | None = None,
    build_max_iterations: int = 5,
    build_exit_reason: str | None = None,
    build_md: bool = False,
) -> pathlib.Path:
    """Write metadata.yaml for a fake run. Returns the run dir."""
    rd = root / "runs" / run_id
    rd.mkdir(parents=True)
    now = updated_at or dt.datetime.now().astimezone()
    created = created_at or now

    iters = "null" if build_iterations is None else str(build_iterations)
    exit_reason = "null" if build_exit_reason is None else f'"{build_exit_reason}"'
    tp = "null" if tests_passed is None else ("true" if tests_passed else "false")
    rc = "true" if review_completed else "false"
    qc = "true" if qa_completed else "false"

    body = textwrap.dedent(f"""\
        schema_version: 1
        run_id: "{run_id}"
        status: {status}
        created_at: "{_iso(created)}"
        updated_at: "{_iso(now)}"
        target:
          repo:
            mode: existing
            path: /tmp/{repo_name}
            name: {repo_name}
            base_ref: main
            fingerprint: null
            created_by_run: null
          worktree:
            name: {worktree_name}
            path: /tmp/wt-{worktree_name}
            branch_name: {branch}
            created: true
            base_ref: main
            initial_commit_sha: null
        scope:
          kind: implementation
          summary: ""
        artifacts:
          raw_idea: raw-idea.md
          answers: null
          brief: null
          plan: null
          preflight: null
          assumptions: null
          decisions: null
          implementation_summary: null
          diff_summary: null
          review_report: null
          qa_report: null
          audit: null
          handoff: null
          followups: null
        validation:
          required: true
          review_completed: {rc}
          qa_completed: {qc}
          qa_recorded: false
          tests_passed: {tp}
          known_issues_count: {known_issues_count}
        completion:
          accepted_by: null
          completion_ref: null
          completed_at: null
          abandoned_reason: null
        build:
          iterations: {iters}
          exit_reason: {exit_reason}
          max_iterations: {build_max_iterations}
        """)
    (rd / "metadata.yaml").write_text(body)

    if build_md:
        stages = rd / "stages" / "4_building"
        stages.mkdir(parents=True)
        (stages / "build.md").write_text("# build\n")
    return rd


def append_event(rd: pathlib.Path, ev: dict) -> None:
    p = rd / "events.jsonl"
    with p.open("a") as f:
        f.write(json.dumps(ev) + "\n")


def base_event(
    seq: int,
    run_id: str,
    event_type: str,
    *,
    status: str = "building",
    at: dt.datetime | None = None,
    actor_name: str = "tim",
    payload: dict | None = None,
    extra: dict | None = None,
) -> dict:
    when = at or dt.datetime.now().astimezone()
    ev = {
        "schema_version": 1,
        "seq": seq,
        "event_id": f"evt_test_{seq:04d}",
        "run_id": run_id,
        "at": _iso(when),
        "actor": {"type": "agent", "name": actor_name},
        "type": event_type,
        "status": status,
        "payload": payload or {},
    }
    if extra:
        ev.update(extra)
    return ev


class BoardSnapshotTestBase(unittest.TestCase):
    def setUp(self):
        reset_caches()
        self.tmp = make_tmp_workbench()
        import sys
        if str(self.tmp) not in sys.path:
            sys.path.insert(0, str(self.tmp))
        from lib import config as cfg_mod
        self.cfg = cfg_mod.load(self.tmp)

    def tearDown(self):
        cleanup(self.tmp)


class TestColumnsAndOrdering(BoardSnapshotTestBase):
    def test_canonical_order(self):
        from lib.board import snapshot

        seed_run(self.tmp, "r-building", status="building", repo_name="alpha")
        seed_run(self.tmp, "r-draft", status="draft", repo_name="beta")
        seed_run(self.tmp, "r-planning", status="planning", repo_name="gamma")

        snap = snapshot.build(self.cfg)
        # All canonical columns present.
        statuses = [c.status for c in snap.columns]
        self.assertEqual(statuses, list(snapshot.COLUMN_ORDER))

        # Visible columns drop empties.
        visible = [c.status for c in snap.visible_columns()]
        # canonical order: draft, planning, building
        self.assertEqual(visible, ["draft", "planning", "building"])

    def test_terminal_states_hidden_by_default(self):
        from lib.board import snapshot

        seed_run(self.tmp, "r-active", status="building")
        seed_run(self.tmp, "r-done", status="done")

        snap = snapshot.build(self.cfg)
        ids = {r.run_id for c in snap.visible_columns() for r in c.runs}
        self.assertIn("r-active", ids)
        self.assertNotIn("r-done", ids)

    def test_terminal_states_with_show_all(self):
        from lib.board import snapshot

        seed_run(self.tmp, "r-done", status="done")
        seed_run(self.tmp, "r-abandoned", status="abandoned")

        snap = snapshot.build(self.cfg, show_all=True)
        ids = {r.run_id for c in snap.visible_columns() for r in c.runs}
        self.assertEqual(ids, {"r-done", "r-abandoned"})

    def test_status_filter(self):
        from lib.board import snapshot

        seed_run(self.tmp, "r-build", status="building")
        seed_run(self.tmp, "r-plan", status="planning")

        snap = snapshot.build(self.cfg, only_status="building")
        ids = {r.run_id for c in snap.visible_columns() for r in c.runs}
        self.assertEqual(ids, {"r-build"})

    def test_within_column_oldest_first(self):
        from lib.board import snapshot

        now = dt.datetime.now().astimezone()
        seed_run(self.tmp, "r-fresh", status="building",
                 updated_at=now - dt.timedelta(minutes=2))
        seed_run(self.tmp, "r-old", status="building",
                 updated_at=now - dt.timedelta(hours=3))

        snap = snapshot.build(self.cfg, now=now)
        building = next(c for c in snap.columns if c.status == "building")
        order = [r.run_id for r in building.runs]
        self.assertEqual(order, ["r-old", "r-fresh"])


class TestHealthFlags(BoardSnapshotTestBase):
    def test_stale_human_review(self):
        from lib.board import snapshot

        stale = dt.datetime.now().astimezone() - dt.timedelta(hours=48)
        fresh = dt.datetime.now().astimezone() - dt.timedelta(hours=1)
        seed_run(self.tmp, "r-stale", status="human_review", updated_at=stale)
        seed_run(self.tmp, "r-fresh", status="human_review", updated_at=fresh)

        snap = snapshot.build(self.cfg)
        runs_by_id = {r.run_id: r for c in snap.columns for r in c.runs}
        self.assertTrue(runs_by_id["r-stale"].is_stale_human_review)
        self.assertFalse(runs_by_id["r-fresh"].is_stale_human_review)

    def test_failing_tests_flag(self):
        from lib.board import snapshot

        seed_run(self.tmp, "r-fail", status="validating",
                 tests_passed=False, known_issues_count=2)
        snap = snapshot.build(self.cfg)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertTrue(r.failing_tests)
        self.assertTrue(r.has_known_issues)
        self.assertEqual(r.known_issues_count, 2)

    def test_builder_gave_up(self):
        from lib.board import snapshot

        seed_run(self.tmp, "r-stop", status="validating",
                 build_iterations=5, build_exit_reason="max_iterations")
        snap = snapshot.build(self.cfg)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertTrue(r.builder_gave_up)


class TestBuildProgress(BoardSnapshotTestBase):
    def test_build_progress_fields(self):
        from lib.board import snapshot

        seed_run(
            self.tmp, "r-build", status="building",
            build_iterations=2, build_max_iterations=5,
            build_md=True,
        )
        snap = snapshot.build(self.cfg)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertEqual(r.build_iterations, 2)
        self.assertEqual(r.build_max_iterations, 5)
        self.assertTrue(r.build_md_exists)


class TestRecentEvents(BoardSnapshotTestBase):
    def test_recent_events_newest_first(self):
        from lib.board import snapshot

        rd = seed_run(self.tmp, "r-evt", status="building")
        now = dt.datetime.now().astimezone()
        append_event(rd, base_event(
            1, "r-evt", "TransitionApplied",
            status="building",
            at=now - dt.timedelta(seconds=30),
            extra={"from": "ready", "to": "building"},
        ))
        append_event(rd, base_event(
            2, "r-evt", "ArtifactWritten",
            status="building",
            at=now - dt.timedelta(seconds=10),
            payload={"artifact_key": "implementation_summary",
                     "path": "/tmp/r-evt/build.md"},
        ))
        append_event(rd, base_event(
            3, "r-evt", "CommandRun",
            status="building",
            at=now - dt.timedelta(seconds=5),
            payload={"command": "pytest", "cwd": "/tmp", "exit_code": 0},
        ))

        snap = snapshot.build(self.cfg, now=now)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        types = [e.type for e in r.recent_events]
        # newest first
        self.assertEqual(types[0], "CommandRun")
        self.assertEqual(types[1], "ArtifactWritten")
        # the ArtifactWritten detail names the file
        self.assertIn("build.md", r.recent_events[1].detail)

    def test_time_in_stage_from_last_transition(self):
        from lib.board import snapshot

        rd = seed_run(self.tmp, "r-stg", status="validating")
        now = dt.datetime.now().astimezone()
        append_event(rd, base_event(
            1, "r-stg", "TransitionApplied",
            status="validating",
            at=now - dt.timedelta(minutes=15),
            extra={"from": "building", "to": "validating"},
        ))
        # Another event later (artifact write) — must not reset time-in-stage.
        append_event(rd, base_event(
            2, "r-stg", "ArtifactWritten",
            status="validating",
            at=now - dt.timedelta(seconds=30),
            payload={"artifact_key": "review_report", "path": "/tmp/r-stg/review.md"},
        ))

        snap = snapshot.build(self.cfg, now=now)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertIsNotNone(r.time_in_stage_seconds)
        # ~15 minutes since the transition.
        self.assertGreaterEqual(r.time_in_stage_seconds, 14 * 60)
        self.assertLessEqual(r.time_in_stage_seconds, 16 * 60)

    def test_bounce_count_and_reason(self):
        from lib.board import snapshot

        rd = seed_run(self.tmp, "r-bnc", status="building")
        now = dt.datetime.now().astimezone()
        append_event(rd, base_event(
            1, "r-bnc", "BounceRequested",
            status="human_review",
            at=now - dt.timedelta(hours=2),
            payload={"bounce_reason": "edge cases missing"},
        ))
        append_event(rd, base_event(
            2, "r-bnc", "BounceRequested",
            status="human_review",
            at=now - dt.timedelta(minutes=10),
            payload={"bounce_reason": "tests too thin"},
        ))

        snap = snapshot.build(self.cfg, now=now)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertEqual(r.bounce_count, 2)
        self.assertEqual(r.recent_bounce_reason, "tests too thin")

    def test_recent_error_after_transition(self):
        from lib.board import snapshot

        rd = seed_run(self.tmp, "r-err", status="building")
        now = dt.datetime.now().astimezone()
        # Transition then error AFTER the transition: counts as recent.
        append_event(rd, base_event(
            1, "r-err", "TransitionApplied",
            status="building",
            at=now - dt.timedelta(minutes=10),
            extra={"from": "ready", "to": "building"},
        ))
        append_event(rd, base_event(
            2, "r-err", "ErrorRecorded",
            status="building",
            at=now - dt.timedelta(minutes=2),
            payload={"error_kind": "GitError", "message": "merge conflict"},
        ))

        snap = snapshot.build(self.cfg, now=now)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertTrue(r.has_recent_error)

    def test_error_before_transition_is_not_recent(self):
        from lib.board import snapshot

        rd = seed_run(self.tmp, "r-err2", status="building")
        now = dt.datetime.now().astimezone()
        # Error first, then transition: the transition clears "recent error".
        append_event(rd, base_event(
            1, "r-err2", "ErrorRecorded",
            status="ready",
            at=now - dt.timedelta(hours=2),
            payload={"error_kind": "X", "message": "y"},
        ))
        append_event(rd, base_event(
            2, "r-err2", "TransitionApplied",
            status="building",
            at=now - dt.timedelta(hours=1),
            extra={"from": "ready", "to": "building"},
        ))

        snap = snapshot.build(self.cfg, now=now)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertFalse(r.has_recent_error)


class TestFollowupsCount(BoardSnapshotTestBase):
    def test_followups_count_from_event(self):
        from lib.board import snapshot

        rd = seed_run(self.tmp, "r-fu", status="followups")
        now = dt.datetime.now().astimezone()
        append_event(rd, base_event(
            1, "r-fu", "FollowupsRecorded",
            status="followups",
            at=now - dt.timedelta(minutes=2),
            payload={
                "followups_path": "/tmp/r-fu/follow-ups.md",
                "entry_count": 4,
                "categories": ["bug_risk", "docs"],
            },
        ))

        snap = snapshot.build(self.cfg, now=now)
        r = next(iter(rr for c in snap.columns for rr in c.runs))
        self.assertEqual(r.followups_entry_count, 4)


class TestMalformedRunSkipped(BoardSnapshotTestBase):
    def test_bad_metadata_yaml_skipped(self):
        from lib.board import snapshot

        seed_run(self.tmp, "r-good", status="building")
        bad = self.tmp / "runs" / "r-bad"
        bad.mkdir(parents=True)
        (bad / "metadata.yaml").write_text("not: [valid: yaml")

        snap = snapshot.build(self.cfg)
        ids = {r.run_id for c in snap.columns for r in c.runs}
        self.assertIn("r-good", ids)
        self.assertNotIn("r-bad", ids)


class TestFormatAge(unittest.TestCase):
    def test_buckets(self):
        from lib.board.snapshot import format_age
        self.assertEqual(format_age(0), "0m")
        self.assertEqual(format_age(59), "0m")
        self.assertEqual(format_age(90), "1m")
        self.assertEqual(format_age(60 * 60), "1h")
        self.assertEqual(format_age(2 * 60 * 60), "2h")
        self.assertEqual(format_age(25 * 60 * 60), "1d")
        self.assertEqual(format_age(48 * 60 * 60), "2d")


if __name__ == "__main__":
    unittest.main()
