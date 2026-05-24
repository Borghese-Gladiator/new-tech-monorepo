"""End-to-end tests (TODO §1).

Drive a run from `new-run` through to a terminal state using the
`AGENT_WORKBENCH_STUB_LLM` env-var mode. The slash command bodies stay
unchanged; the CLI's `--init` step copies fixture artifacts from
`tests/fixtures/e2e/<scenario>/` in place of an LLM authoring them.

Three scenarios live here:

  TestE2EHappyPath   — new-run → ... → complete, no bounce.
  TestE2EBounceLoop  — happy path, then bounce, then re-validate, complete.
  TestE2EAbandon     — abandon at several non-terminal states.

Adding a new scenario is documented in `tests/README.md`.
"""
from __future__ import annotations

import json
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
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "e2e"


def cli(workbench_root: pathlib.Path, *args, stub_fixture: pathlib.Path | None = None,
        input_text: str | None = None) -> subprocess.CompletedProcess:
    """Run the CLI as a subprocess, optionally with a stub-LLM fixture dir."""
    env = os.environ.copy()
    env["AGENT_WORKBENCH_ROOT"] = str(workbench_root)
    if stub_fixture is not None:
        env["AGENT_WORKBENCH_STUB_LLM"] = str(stub_fixture)
    else:
        env.pop("AGENT_WORKBENCH_STUB_LLM", None)
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(workbench_root), *args],
        capture_output=True, text=True, env=env,
        input=input_text,
    )


def make_throwaway_repo() -> pathlib.Path:
    repo = pathlib.Path(tempfile.mkdtemp(prefix="aw-e2e-repo-"))
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    # Drop a bin/cli stub so the fixture's `Files likely to change` claim
    # against bin/cli has a target. The committed bin/cli is empty; the
    # building stage's fixture will mutate the file in the worktree.
    (repo / "bin").mkdir()
    (repo / "bin" / "cli").write_text("#!/usr/bin/env bash\n# stub\n")
    (repo / "bin" / "cli").chmod(0o755)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([
        "git", "-C", str(repo),
        "-c", "user.name=test", "-c", "user.email=test@x",
        "commit", "-q", "-m", "init",
    ], check=True)
    return repo


def read_events(run_dir: pathlib.Path) -> list[dict]:
    path = run_dir / "events.jsonl"
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def event_types(events_: list[dict]) -> list[str]:
    return [e["type"] for e in events_]


def transitions_seen(events_: list[dict]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for e in events_:
        if e.get("type") != "TransitionApplied":
            continue
        out.append((e.get("from"), e.get("to")))
    return out


class E2ECase(unittest.TestCase):
    """Base class: spins up a workbench root + a throwaway repo per test."""

    def setUp(self):
        self.tmp = make_tmp_workbench()
        # Copy bin/ + lib/ so the CLI can import from sys.path.
        shutil.copytree(ROOT / "bin", self.tmp / "bin")
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

    def _new_run(self, fixture: pathlib.Path, slug: str = "e2e-smoke") -> tuple[str, pathlib.Path, pathlib.Path]:
        """Create a run from `fixture/raw-idea.md`. Returns (run_id, run_dir, repo)."""
        repo = self._repo()
        idea = fixture / "raw-idea.md"
        self.assertTrue(idea.exists(), f"fixture missing raw-idea.md: {idea}")
        r = cli(
            self.tmp, "new-run",
            "--repo-path", str(repo),
            "--worktree-name", slug,
            "--base-ref", "main",
            "--idea-file", str(idea),
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        run_id = r.stdout.strip()
        return run_id, self.tmp / "runs" / run_id, repo


class TestE2EHappyPath(E2ECase):
    """new-run → shape → plan → start → validate → followups → complete."""

    def test_happy_path(self):
        fixture = FIXTURES / "happy"
        run_id, run_dir, repo = self._new_run(fixture, slug="happy-smoke")

        # shape --init + finalize, both with stub-LLM on.
        r = cli(self.tmp, "shape", run_id, "--init", stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertTrue((run_dir / "brief.md").exists())
        # Confirm the fixture's content actually landed (not the template).
        self.assertIn("Hello command", (run_dir / "brief.md").read_text())

        r = cli(self.tmp, "shape", run_id, stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("shaping -> planning", r.stdout)

        # plan --init + finalize.
        r = cli(self.tmp, "plan", run_id, "--init", stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("Hello command", (run_dir / "plan.md").read_text())

        r = cli(self.tmp, "plan", run_id, stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("planning -> ready", r.stdout)

        # start (no LLM).
        r = cli(self.tmp, "start", run_id, "--approved-by", "e2e-tester",
                stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("ready -> building", r.stdout)

        # validate --init: materializes build.md + validating fixtures.
        r = cli(self.tmp, "validate", run_id, "--init", stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("building -> validating", r.stdout)
        # build.md got moved into stages/4_building/ by the transition engine.
        self.assertTrue((run_dir / "stages" / "4_building" / "build.md").exists())
        # validating-stage templates were overwritten by the fixtures.
        self.assertIn("approve", (run_dir / "review.md").read_text().lower())

        # validate finalize: validating -> followups.
        r = cli(self.tmp, "validate", run_id,
                "--tests-passed", "true", "--known-issues", "0",
                stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("validating -> followups", r.stdout)
        self.assertTrue((run_dir / "audit.md").exists())

        # followups default mode: materializes follow-ups.md + transitions.
        r = cli(self.tmp, "followups", run_id, stub_fixture=fixture)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("followups -> human_review", r.stdout)
        # TODO §2 AC2: the absolute path to HUMAN_REVIEW.md must appear in
        # stdout so the reviewer can click it from the terminal.
        self.assertIn(str(run_dir / "HUMAN_REVIEW.md"), r.stdout)

        # complete.
        r = cli(self.tmp, "complete", run_id, "--accepted-by", "e2e-tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("human_review -> done", r.stdout)

        # Final state: every stage-promoted artifact is in place.
        self.assertTrue((run_dir / "stages" / "2_shaping" / "brief.md").exists())
        self.assertTrue((run_dir / "stages" / "3_planning" / "plan.md").exists())
        self.assertTrue((run_dir / "stages" / "4_building" / "build.md").exists())
        self.assertTrue((run_dir / "stages" / "5_validating" / "review.md").exists())
        self.assertTrue((run_dir / "stages" / "5_validating" / "qa" / "report.md").exists())
        self.assertTrue((run_dir / "stages" / "6_followups" / "follow-ups.md").exists())
        self.assertTrue((run_dir / "HUMAN_REVIEW.md").exists())

        # Event ordering: every staged transition fired in order.
        evs = read_events(run_dir)
        self.assertEqual(
            transitions_seen(evs),
            [
                ("draft", "shaping"),
                ("shaping", "planning"),
                ("planning", "ready"),
                ("ready", "building"),
                ("building", "validating"),
                ("validating", "followups"),
                ("followups", "human_review"),
                ("human_review", "done"),
            ],
        )
        # Key non-transition events all show up.
        types = event_types(evs)
        for required in ("RunCreated", "PreflightCompleted", "ReviewCompleted",
                         "QACompleted", "AuditRendered", "FollowupsRecorded",
                         "HumanHandoffCreated"):
            self.assertIn(required, types, msg=f"missing event: {required}")


class TestE2EBounceLoop(E2ECase):
    """Drive the happy path, then bounce back to building, then complete."""

    def test_bounce_loop(self):
        fix1 = FIXTURES / "bounce_pass1"
        fix2 = FIXTURES / "bounce_pass2"
        run_id, run_dir, repo = self._new_run(fix1, slug="bounce-smoke")

        # Drive pass 1 with the pass-1 fixture set (review.md says
        # request_changes; reviewer would normally bounce after, but our
        # CLI doesn't fail validate on a request_changes review — that's
        # an upstream policy question, not a state-machine gate). We
        # finalize through to human_review so we can then exercise bounce.
        cli(self.tmp, "shape", run_id, "--init", stub_fixture=fix1)
        cli(self.tmp, "shape", run_id, stub_fixture=fix1)
        cli(self.tmp, "plan", run_id, "--init", stub_fixture=fix1)
        cli(self.tmp, "plan", run_id, stub_fixture=fix1)
        cli(self.tmp, "start", run_id, "--approved-by", "tester")
        cli(self.tmp, "validate", run_id, "--init", stub_fixture=fix1)
        # known-issues=1 so the validation block records the v1 gap.
        cli(self.tmp, "validate", run_id, "--tests-passed", "false",
            "--known-issues", "1", stub_fixture=fix1)
        cli(self.tmp, "followups", run_id, stub_fixture=fix1)

        # Now bounce back to building.
        r = cli(self.tmp, "bounce", run_id,
                "--reason", "AC-1 not covered",
                "--requested-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("human_review -> building", r.stdout)

        # Pass-1 building/validating outputs should be archived as -v1.
        self.assertTrue((run_dir / "archive" / "4_building" / "build-v1.md").exists())
        self.assertTrue((run_dir / "archive" / "5_validating" / "review-v1.md").exists())

        # Drive pass 2 with the pass-2 fixture set.
        cli(self.tmp, "validate", run_id, "--init", stub_fixture=fix2)
        cli(self.tmp, "validate", run_id, "--tests-passed", "true",
            "--known-issues", "0", stub_fixture=fix2)
        r = cli(self.tmp, "followups", run_id, stub_fixture=fix2)
        # TODO §2 AC2: stdout from the post-bounce followups call carries
        # the absolute HUMAN_REVIEW.md path too.
        self.assertIn(str(run_dir / "HUMAN_REVIEW.md"), r.stdout)

        # human_review -> done.
        r = cli(self.tmp, "complete", run_id, "--accepted-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("human_review -> done", r.stdout)

        evs = read_events(run_dir)
        # The bounce loop produces two passes through building/validating.
        ts = transitions_seen(evs)
        self.assertEqual(ts.count(("ready", "building")), 1)  # only one initial start
        self.assertEqual(ts.count(("building", "validating")), 2)
        self.assertEqual(ts.count(("validating", "followups")), 2)
        self.assertEqual(ts.count(("followups", "human_review")), 2)
        self.assertEqual(ts.count(("human_review", "building")), 1)
        self.assertEqual(ts.count(("human_review", "done")), 1)
        # BounceRequested with the reason is present.
        bounces = [e for e in evs if e["type"] == "BounceRequested"]
        self.assertEqual(len(bounces), 1)
        self.assertIn("AC-1", bounces[0]["payload"]["bounce_reason"])


class TestE2EAbandon(E2ECase):
    """Abandon at three non-terminal states to confirm `*->abandoned` works
    regardless of where the run is."""

    def test_abandon_at_shaping(self):
        fixture = FIXTURES / "happy"
        run_id, run_dir, _ = self._new_run(fixture, slug="abandon-shaping")
        cli(self.tmp, "shape", run_id, "--init", stub_fixture=fixture)

        r = cli(self.tmp, "abandon", run_id,
                "--reason", "scope shrank", "--abandoned-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)

        r = cli(self.tmp, "show", run_id)
        self.assertIn("status:     abandoned", r.stdout)

        evs = read_events(run_dir)
        ts = transitions_seen(evs)
        self.assertIn(("shaping", "abandoned"), ts)

    def test_abandon_at_building(self):
        fixture = FIXTURES / "happy"
        run_id, run_dir, _ = self._new_run(fixture, slug="abandon-building")
        cli(self.tmp, "shape", run_id, "--init", stub_fixture=fixture)
        cli(self.tmp, "shape", run_id, stub_fixture=fixture)
        cli(self.tmp, "plan", run_id, "--init", stub_fixture=fixture)
        cli(self.tmp, "plan", run_id, stub_fixture=fixture)
        cli(self.tmp, "start", run_id, "--approved-by", "tester")

        r = cli(self.tmp, "abandon", run_id,
                "--reason", "blocked on dep", "--abandoned-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)

        r = cli(self.tmp, "show", run_id)
        self.assertIn("status:     abandoned", r.stdout)

        evs = read_events(run_dir)
        ts = transitions_seen(evs)
        self.assertIn(("building", "abandoned"), ts)

    def test_abandon_at_draft(self):
        # No fixture artifacts needed: abandoning a fresh run.
        fixture = FIXTURES / "happy"
        run_id, run_dir, _ = self._new_run(fixture, slug="abandon-draft")

        r = cli(self.tmp, "abandon", run_id,
                "--reason", "duplicate idea", "--abandoned-by", "tester")
        self.assertEqual(r.returncode, 0, msg=r.stderr)

        r = cli(self.tmp, "show", run_id)
        self.assertIn("status:     abandoned", r.stdout)

        evs = read_events(run_dir)
        ts = transitions_seen(evs)
        self.assertIn(("draft", "abandoned"), ts)


if __name__ == "__main__":
    unittest.main()
