"""CLI smoke tests for `agent-workbench board --static`.

The default `board` invocation launches a Textual TUI (lib/board/app.py) which
can't be driven from a non-interactive test runner. The structural assertions
about grouping, ordering, terminal-state hiding, and stale flagging now live
in tests/test_board_snapshot.py against lib/board/snapshot.py directly.

This file keeps the end-to-end CLI smoke against the `--static` fallback path
so we know the subprocess wiring still works and the static dump is callable
without third-party deps installed.
"""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
import unittest

from tests._helpers import make_tmp_workbench, cleanup

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "agent-workbench"


def cli(workbench_root: pathlib.Path, *args) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["AGENT_WORKBENCH_ROOT"] = str(workbench_root)
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(workbench_root), *args],
        capture_output=True, text=True, env=env,
    )


def _iso(ts: dt.datetime) -> str:
    return ts.astimezone().replace(microsecond=0).isoformat()


def write_run(
    root: pathlib.Path,
    run_id: str,
    *,
    status: str,
    repo_name: str = "repo",
    branch: str = "agent/branch",
    updated_at: dt.datetime | None = None,
) -> None:
    rd = root / "runs" / run_id
    rd.mkdir(parents=True)
    now = updated_at or dt.datetime.now().astimezone()
    body = textwrap.dedent(f"""\
        schema_version: 1
        run_id: "{run_id}"
        status: {status}
        created_at: "{_iso(now)}"
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
            name: wt
            path: /tmp/wt
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
        validation:
          required: true
          review_completed: false
          qa_completed: false
          qa_recorded: false
          tests_passed: null
          known_issues_count: 0
        completion:
          accepted_by: null
          completion_ref: null
          completed_at: null
          abandoned_reason: null
        """)
    (rd / "metadata.yaml").write_text(body)


class BoardCase(unittest.TestCase):
    def setUp(self):
        self.tmp = make_tmp_workbench()
        shutil.copytree(ROOT / "bin", self.tmp / "bin")
        shutil.copytree(ROOT / "lib", self.tmp / "lib")

    def tearDown(self):
        cleanup(self.tmp)


class TestEmpty(BoardCase):
    def test_empty_workbench(self):
        r = cli(self.tmp, "board", "--static")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("(no runs)", r.stdout)


class TestStaticDumpStructure(BoardCase):
    def test_columns_appear_in_canonical_order(self):
        write_run(self.tmp, "r-building", status="building", repo_name="alpha")
        write_run(self.tmp, "r-draft", status="draft", repo_name="beta")
        write_run(self.tmp, "r-planning", status="planning", repo_name="gamma")

        r = cli(self.tmp, "board", "--static")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        out = r.stdout
        i_draft = out.find("draft")
        i_planning = out.find("planning")
        i_building = out.find("building")
        self.assertGreater(i_draft, -1, out)
        self.assertGreater(i_planning, i_draft, out)
        self.assertGreater(i_building, i_planning, out)
        self.assertIn("r-draft", out)
        self.assertIn("r-planning", out)
        self.assertIn("r-building", out)

    def test_terminal_states_hidden_by_default(self):
        write_run(self.tmp, "r-active", status="building")
        write_run(self.tmp, "r-done", status="done")

        r = cli(self.tmp, "board", "--static")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("r-active", r.stdout)
        self.assertNotIn("r-done", r.stdout)

    def test_terminal_states_with_all(self):
        write_run(self.tmp, "r-done", status="done")
        write_run(self.tmp, "r-abandoned", status="abandoned")

        r = cli(self.tmp, "board", "--static", "--all")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("r-done", r.stdout)
        self.assertIn("r-abandoned", r.stdout)

    def test_status_filter(self):
        write_run(self.tmp, "r-build", status="building")
        write_run(self.tmp, "r-plan", status="planning")

        r = cli(self.tmp, "board", "--static", "--status", "building")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("r-build", r.stdout)
        self.assertNotIn("r-plan", r.stdout)


class TestStaleHumanReviewStatic(BoardCase):
    def test_stale_marker_and_footer(self):
        fresh = dt.datetime.now().astimezone() - dt.timedelta(hours=1)
        stale = dt.datetime.now().astimezone() - dt.timedelta(hours=48)
        write_run(self.tmp, "r-fresh", status="human_review",
                  updated_at=fresh, repo_name="r1")
        write_run(self.tmp, "r-stale", status="human_review",
                  updated_at=stale, repo_name="r2")

        r = cli(self.tmp, "board", "--static")
        self.assertEqual(r.returncode, 0, msg=r.stderr)

        self.assertIn("r-fresh", r.stdout)
        self.assertIn("r-stale", r.stdout)
        self.assertIn("! r-stale", r.stdout)
        self.assertNotIn("! r-fresh", r.stdout)

        self.assertIn("Stale human_review:", r.stdout)
        footer_start = r.stdout.find("Stale human_review:")
        footer = r.stdout[footer_start:]
        self.assertIn("r-stale", footer)
        self.assertNotIn("r-fresh", footer)


class TestUnreadableRunSkippedStatic(BoardCase):
    def test_bad_metadata_is_skipped_not_fatal(self):
        write_run(self.tmp, "r-good", status="building")
        bad = self.tmp / "runs" / "r-bad"
        bad.mkdir(parents=True)
        (bad / "metadata.yaml").write_text("not: [valid: yaml")

        r = cli(self.tmp, "board", "--static")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("r-good", r.stdout)
        self.assertNotIn("r-bad", r.stdout)


def _make_snapshot(**overrides):
    """Construct a RunSnapshot with sane defaults for the static-renderer
    tests. Every required field has a default; tests override what they
    care about."""
    from lib.board.source import RunSnapshot

    defaults = dict(
        run_id="r-1",
        status="building",
        scope_kind="implementation",
        repo_name="alpha",
        repo_path="/tmp/alpha",
        repo_path_tail="tmp/alpha",
        branch_name="agent/x",
        worktree_name="wt",
        run_dir="/tmp/runs/r-1",
        worktree_path="/tmp/wt-1",
        created_at="2026-05-22T00:00:00-04:00",
        updated_at="2026-05-22T00:00:00-04:00",
        age_seconds=0.0,
        total_age_seconds=0.0,
        time_in_stage_seconds=None,
        is_live=False,
        build_iterations=None,
        build_max_iterations=None,
        build_exit_reason=None,
        build_md_exists=False,
        avg_iteration_seconds=None,
        ac_total=None,
        ac_covered=None,
        ac_table_missing=False,
        diff_added=None,
        diff_removed=None,
        diff_files=None,
        review_completed=False,
        qa_completed=False,
        tests_passed=None,
        known_issues_count=0,
        tests_recorded_age_seconds=None,
        followups_entry_count=None,
        followups_categories=(),
        is_stale_human_review=False,
        builder_gave_up=False,
        failing_tests=False,
        has_known_issues=False,
        has_recent_error=False,
        bounce_count=0,
        recent_bounce_reason=None,
        bounced_from=None,
        bounced_at_age_seconds=None,
        worktree_missing=False,
        completed_at=None,
        accepted_by=None,
        abandoned_reason=None,
        recent_events=(),
    )
    defaults.update(overrides)
    return RunSnapshot(**defaults)


class TestStaticCardStack(unittest.TestCase):
    """Direct unit tests for lib/cli/cmd_board._static_card_stack.

    These cover the status-aware rendering branches that the subprocess
    smoke tests above can't easily assert against (the subprocess relies on
    `metadata.list_runs` scanning a tmp dir).
    """

    def test_human_review_includes_followups_category_breakdown(self):
        """Regression: the dogfood run (2026-05-22-s2-attrs) showed that
        the static renderer's `human_review` branch wrote `follow-ups: 3`
        but skipped the per-category breakdown lines. The Textual
        renderer was already correct via the shared helper; the static
        path drifted. Lock the fix in so it can't silently regress."""
        from lib.cli.cmd_board import _static_card_stack

        run = _make_snapshot(
            status="human_review",
            followups_entry_count=3,
            followups_categories=(
                ("scope_extension", 1),
                ("bug_risk", 1),
                ("docs", 1),
            ),
        )
        lines = _static_card_stack(run)
        body = "\n".join(lines)
        self.assertIn("follow-ups: 3", body)
        self.assertIn("1 scope_extension", body)
        self.assertIn("1 bug_risk", body)
        self.assertIn("1 docs", body)

    def test_followups_status_also_includes_breakdown(self):
        """Sanity: the followups column has always rendered the
        breakdown; assert it still does so the two branches stay in
        sync."""
        from lib.cli.cmd_board import _static_card_stack

        run = _make_snapshot(
            status="followups",
            followups_entry_count=2,
            followups_categories=(("tech_debt", 2),),
        )
        body = "\n".join(_static_card_stack(run))
        self.assertIn("follow-ups: 2", body)
        self.assertIn("2 tech_debt", body)

    def test_human_review_without_followups_omits_lines(self):
        """No follow-up data → no follow-up lines (avoid empty noise)."""
        from lib.cli.cmd_board import _static_card_stack

        run = _make_snapshot(status="human_review")
        body = "\n".join(_static_card_stack(run))
        self.assertNotIn("follow-ups:", body)


if __name__ == "__main__":
    unittest.main()
