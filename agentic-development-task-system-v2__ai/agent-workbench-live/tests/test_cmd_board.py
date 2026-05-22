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


if __name__ == "__main__":
    unittest.main()
