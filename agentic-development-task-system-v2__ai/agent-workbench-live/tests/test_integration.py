"""Integration tests.

Spin up a temp workbench root + a throwaway git repo, drive the CLI end-to-end,
assert filesystem state and event log after each step.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests._helpers import make_tmp_workbench, cleanup, reset_caches  # noqa: F401

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "agent-workbench"


def cli(workbench_root: pathlib.Path, *args, input_text: str | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["AGENT_WORKBENCH_ROOT"] = str(workbench_root)
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(workbench_root), *args],
        capture_output=True, text=True, env=env,
        input=input_text,
    )


def make_throwaway_repo() -> pathlib.Path:
    repo = pathlib.Path(tempfile.mkdtemp(prefix="aw-repo-"))
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    (repo / "README.md").write_text("# throwaway\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([
        "git", "-C", str(repo),
        "-c", "user.name=test", "-c", "user.email=test@x",
        "commit", "-q", "-m", "init",
    ], check=True)
    return repo


class IntegrationCase(unittest.TestCase):
    def setUp(self):
        self.tmp = make_tmp_workbench()
        # Copy bin/ into the temp workbench so AGENT_WORKBENCH_ROOT works for the CLI.
        shutil.copytree(ROOT / "bin", self.tmp / "bin")
        # And lib/, since the CLI imports from sys.path == workbench root.
        shutil.copytree(ROOT / "lib", self.tmp / "lib")
        self.repos: list[pathlib.Path] = []

    def tearDown(self):
        cleanup(self.tmp)
        for r in self.repos:
            cleanup(r)

    def _repo(self) -> pathlib.Path:
        r = make_throwaway_repo()
        self.repos.append(r)
        return r


class TestHappyPath(IntegrationCase):
    def test_full_lifecycle(self):
        repo = self._repo()
        idea = self.tmp / "idea.md"
        idea.write_text("Add a hello endpoint to the throwaway repo.\n")

        # new-run
        r = cli(self.tmp, "new-run",
                "--repo-path", str(repo),
                "--worktree-name", "hello-endpoint",
                "--idea-file", str(idea))
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        run_id = r.stdout.strip()
        self.assertTrue(run_id)

        # show: confirm draft state
        r = cli(self.tmp, "show", run_id)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("status:     draft", r.stdout)

        # shape --init: draft -> shaping
        r = cli(self.tmp, "shape", run_id, "--init")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("draft -> shaping", r.stdout)

        # Fill brief
        brief = self.tmp / "runs" / run_id / "brief.md"
        brief.write_text("# Brief\n\n## Goal\nAdd a hello endpoint.\n")

        # shape finalize: shaping -> planning
        r = cli(self.tmp, "shape", run_id)
        self.assertEqual(r.returncode, 0, msg=r.stderr)

        # plan --init
        r = cli(self.tmp, "plan", run_id, "--init")
        self.assertEqual(r.returncode, 0, msg=r.stderr)

        # Fill planning artifacts
        run_dir = self.tmp / "runs" / run_id
        (run_dir / "plan.md").write_text("# Plan\nAdd hello.\n")
        (run_dir / "preflight.md").write_text("# Preflight\nOK.\n")
        (run_dir / "assumptions.md").write_text(
            "# Assumptions\n\n## ASM-001\n- **Text**: We use Go.\n- **Reason**: It's a Go repo.\n- **Impact**: low\n"
        )
        (run_dir / "decisions.md").write_text(
            "# Decisions\n\n## DR-001\n- **Decision**: Use net/http.\n- **Rationale**: stdlib is enough.\n"
        )

        # plan finalize: planning -> ready
        r = cli(self.tmp, "plan", run_id)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("planning -> ready", r.stdout)

        # start: ready -> building (creates worktree)
        r = cli(self.tmp, "start", run_id, "--approved-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("ready -> building", r.stdout)

        # The worktree should exist.
        worktree = self.tmp / "worktrees" / repo.name / "hello-endpoint"
        self.assertTrue(worktree.exists(), f"worktree missing at {worktree}")
        self.assertTrue((worktree / "README.md").exists())
        # The branch should exist in the source repo.
        branch_check = subprocess.run(
            ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", "refs/heads/agent/hello-endpoint"]
        )
        self.assertEqual(branch_check.returncode, 0)

        # validate --init: building -> validating
        r = cli(self.tmp, "validate", run_id, "--init")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("building -> validating", r.stdout)

        # Fill post-impl artifacts
        (run_dir / "implementation-summary.md").write_text("# Impl\nAdded /hello.\n")
        (run_dir / "diff-summary.md").write_text("# Diff\nOne file.\n")
        (run_dir / "review.md").write_text("# Review\n\n## Decision\napprove\n")
        (run_dir / "qa" / "report.md").write_text("# QA\nLooks good.\n")
        (run_dir / "handoff.md").write_text("# Handoff\nGo look.\n")

        # validate finalize: validating -> human_review
        r = cli(self.tmp, "validate", run_id, "--tests-passed", "true", "--known-issues", "0")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("validating -> human_review", r.stdout)
        # audit.md was rendered
        self.assertTrue((run_dir / "audit.md").exists())

        # complete: human_review -> done
        r = cli(self.tmp, "complete", run_id, "--accepted-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("human_review -> done", r.stdout)

        # final state
        r = cli(self.tmp, "show", run_id)
        self.assertIn("status:     done", r.stdout)

        # events sanity: TransitionApplied count == 7 (draft->shaping->planning->ready->building->validating->human_review->done)
        r = cli(self.tmp, "events", run_id, "--type", "TransitionApplied")
        self.assertEqual(r.stdout.count("TransitionApplied"), 7, msg=r.stdout)


class TestBounceLoop(IntegrationCase):
    def _drive_to_human_review(self) -> tuple[str, pathlib.Path]:
        """Drive a fresh run to human_review and return (run_id, run_dir)."""
        repo = self._repo()
        idea = self.tmp / f"idea-{repo.name}.md"
        idea.write_text("bounce test\n")

        r = cli(self.tmp, "new-run", "--repo-path", str(repo),
                "--worktree-name", f"bounce-test-{repo.name}",
                "--idea-file", str(idea))
        run_id = r.stdout.strip()
        run_dir = self.tmp / "runs" / run_id

        cli(self.tmp, "shape", run_id, "--init")
        (run_dir / "brief.md").write_text("# Brief\nB.\n")
        cli(self.tmp, "shape", run_id)
        cli(self.tmp, "plan", run_id, "--init")
        for n in ("plan.md", "preflight.md"):
            (run_dir / n).write_text(f"# {n}\nx\n")
        (run_dir / "assumptions.md").write_text("# A\n\n## ASM-001\n- **Text**: x\n")
        (run_dir / "decisions.md").write_text("# D\n\n## DR-001\n- **Decision**: x\n")
        cli(self.tmp, "plan", run_id)
        cli(self.tmp, "start", run_id, "--approved-by", "t")
        cli(self.tmp, "validate", run_id, "--init")
        for n in ("implementation-summary.md", "diff-summary.md", "review.md", "handoff.md"):
            (run_dir / n).write_text(f"# {n}\nx\n")
        (run_dir / "qa" / "report.md").write_text("# QA\nx\n")
        cli(self.tmp, "validate", run_id)
        return run_id, run_dir

    def test_bounce_back_to_building(self):
        run_id, run_dir = self._drive_to_human_review()

        # Backwards-compat: bounce with no --change-request-path still works.
        r = cli(self.tmp, "bounce", run_id,
                "--reason", "needs tests",
                "--requested-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("human_review -> building", r.stdout)
        self.assertNotIn("change-request:", r.stdout)

        # Re-validate
        cli(self.tmp, "validate", run_id, "--init")
        cli(self.tmp, "validate", run_id)

        r = cli(self.tmp, "show", run_id)
        self.assertIn("status:     human_review", r.stdout)

    def test_bounce_with_change_request_path(self):
        run_id, run_dir = self._drive_to_human_review()

        cr_path = run_dir / "change-request.md"
        cr_path.write_text(
            "# Change Request — " + run_id + "\n\n"
            "## Bounce 1 — 2026-05-18T00:00:00Z — tester\n\n"
            "**Scope:** Implementation\n"
        )

        r = cli(self.tmp, "bounce", run_id,
                "--reason", "rework hand evaluator",
                "--requested-by", "tester",
                "--change-request-path", str(cr_path))
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("human_review -> building", r.stdout)
        self.assertIn("change-request:", r.stdout)

        # The BounceRequested event should carry change_request_path in its payload.
        r = cli(self.tmp, "events", run_id, "--type", "BounceRequested", "--raw")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("change_request_path", r.stdout)

    def test_bounce_with_missing_change_request_file_fails(self):
        run_id, run_dir = self._drive_to_human_review()

        missing = run_dir / "change-request.md"  # not created
        r = cli(self.tmp, "bounce", run_id,
                "--reason", "x",
                "--requested-by", "tester",
                "--change-request-path", str(missing))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("change-request file not found", r.stderr + r.stdout)

        # State should not have advanced.
        r = cli(self.tmp, "show", run_id)
        self.assertIn("status:     human_review", r.stdout)

    def test_bounce_with_empty_change_request_file_fails(self):
        run_id, run_dir = self._drive_to_human_review()

        empty = run_dir / "change-request.md"
        empty.write_text("")

        r = cli(self.tmp, "bounce", run_id,
                "--reason", "x",
                "--requested-by", "tester",
                "--change-request-path", str(empty))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("empty", r.stderr + r.stdout)

        r = cli(self.tmp, "show", run_id)
        self.assertIn("status:     human_review", r.stdout)


class TestAbandon(IntegrationCase):
    def test_abandon_at_various_states(self):
        for label, prepare in [
            ("draft", lambda rid, rd: None),
            ("shaping", lambda rid, rd: cli(self.tmp, "shape", rid, "--init")),
        ]:
            repo = self._repo()
            idea = self.tmp / f"idea-{label}.md"
            idea.write_text(f"abandon at {label}\n")
            r = cli(self.tmp, "new-run", "--repo-path", str(repo),
                    "--worktree-name", f"abandon-{label}",
                    "--idea-file", str(idea))
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            rid = r.stdout.strip()
            prepare(rid, self.tmp / "runs" / rid)

            r = cli(self.tmp, "abandon", rid,
                    "--reason", "test", "--abandoned-by", "t")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            r = cli(self.tmp, "show", rid)
            self.assertIn("status:     abandoned", r.stdout)


class TestNewRepo(IntegrationCase):
    def test_new_repo_flow(self):
        new_repo_dir = pathlib.Path(tempfile.mkdtemp(prefix="aw-newrepo-"))
        # Make it empty (mkdtemp creates dir but empty).
        self.repos.append(new_repo_dir)
        idea = self.tmp / "idea.md"
        idea.write_text("bootstrap a thing\n")

        r = cli(self.tmp, "new-run",
                "--new-repo-path", str(new_repo_dir),
                "--worktree-name", "bootstrap",
                "--idea-file", str(idea),
                "--scope-kind", "bootstrap")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        run_id = r.stdout.strip()

        # Repo was created with monorepo scaffold + initial commit.
        self.assertTrue((new_repo_dir / "README.md").exists())
        self.assertTrue((new_repo_dir / "docs").exists())
        self.assertTrue((new_repo_dir / "backend").exists())
        self.assertTrue((new_repo_dir / "frontend").exists())
        # And it is a git repo.
        proc = subprocess.run(["git", "-C", str(new_repo_dir), "log", "--oneline"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("agent-workbench initial scaffold", proc.stdout)

        # Metadata records mode=new and a fingerprint (initial SHA).
        r = cli(self.tmp, "show", run_id)
        self.assertIn("repo.mode:      new", r.stdout)


if __name__ == "__main__":
    unittest.main()
