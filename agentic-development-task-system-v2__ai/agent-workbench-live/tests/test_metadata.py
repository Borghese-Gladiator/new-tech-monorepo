"""Tests for lib/metadata."""
from __future__ import annotations

import unittest

from tests._helpers import make_tmp_workbench, cleanup, reset_caches
from lib import config, metadata


class TestMetadata(unittest.TestCase):
    def setUp(self):
        self.tmp = make_tmp_workbench()
        reset_caches()
        self.cfg = config.load(self.tmp)

    def tearDown(self):
        cleanup(self.tmp)

    def _create_run(self, run_id="2026-05-18-test"):
        return metadata.create(
            self.cfg, run_id,
            repo_mode="existing",
            repo_path="/tmp/x",
            repo_name="x",
            base_ref="HEAD",
            worktree_name="x",
            branch_name="agent/x",
            raw_idea_path="raw-idea.md",
        )

    def test_create_and_load(self):
        meta = self._create_run()
        self.assertEqual(meta["status"], "draft")
        loaded = metadata.load(self.cfg, "2026-05-18-test")
        self.assertEqual(loaded["run_id"], "2026-05-18-test")
        self.assertEqual(loaded["target"]["repo"]["path"], "/tmp/x")

    def test_create_refuses_duplicate(self):
        self._create_run()
        with self.assertRaises(metadata.MetadataError):
            self._create_run()

    def test_load_missing_run(self):
        with self.assertRaises(metadata.MetadataError):
            metadata.load(self.cfg, "no-such-run")

    def test_set_status_valid(self):
        self._create_run()
        metadata.set_status(self.cfg, "2026-05-18-test", "shaping")
        meta = metadata.load(self.cfg, "2026-05-18-test")
        self.assertEqual(meta["status"], "shaping")

    def test_set_status_invalid(self):
        self._create_run()
        with self.assertRaises(metadata.MetadataError):
            metadata.set_status(self.cfg, "2026-05-18-test", "bogus")

    def test_round_trip_preserves_artifacts(self):
        self._create_run()
        def _m(d):
            d["artifacts"]["brief"] = "brief.md"
        metadata.update(self.cfg, "2026-05-18-test", _m)
        meta = metadata.load(self.cfg, "2026-05-18-test")
        self.assertEqual(meta["artifacts"]["brief"], "brief.md")
        self.assertIsNone(meta["artifacts"]["answers"])

    def test_list_runs(self):
        self._create_run("2026-05-18-a")
        self._create_run("2026-05-18-b")
        runs = metadata.list_runs(self.cfg)
        self.assertEqual(runs, ["2026-05-18-a", "2026-05-18-b"])

    def test_create_includes_build_block(self):
        """TODO §1e: new runs have a build: telemetry block."""
        meta = self._create_run("2026-05-20-build")
        self.assertIn("build", meta)
        self.assertIsNone(meta["build"]["iterations"])
        self.assertIsNone(meta["build"]["exit_reason"])
        self.assertEqual(meta["build"]["max_iterations"], 5)

    def test_load_without_build_block_backcompat(self):
        """A flat-layout run.yaml missing the build: key must still load
        (TODO §1e back-compat for pre-renovate runs)."""
        rd = self.cfg.runs_path / "legacy"
        rd.mkdir(parents=True)
        (rd / "metadata.yaml").write_text("""schema_version: 1
run_id: legacy
status: draft
created_at: 2025-12-01T00:00:00
updated_at: 2025-12-01T00:00:00
target:
  repo:
    mode: existing
    path: /tmp/x
    name: x
    base_ref: HEAD
    fingerprint: null
    created_by_run: null
  worktree:
    name: x
    path: null
    branch_name: agent/x
    created: false
    base_ref: HEAD
    initial_commit_sha: null
scope:
  kind: implementation
  summary: ''
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
        loaded = metadata.load(self.cfg, "legacy")
        self.assertEqual(loaded["status"], "draft")
        self.assertNotIn("build", loaded)


if __name__ == "__main__":
    unittest.main()
