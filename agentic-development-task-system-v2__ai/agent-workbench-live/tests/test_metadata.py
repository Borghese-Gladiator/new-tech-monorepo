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


if __name__ == "__main__":
    unittest.main()
