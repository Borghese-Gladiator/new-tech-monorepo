"""Tests for lib/events."""
from __future__ import annotations

import unittest

from tests._helpers import make_tmp_workbench, cleanup, reset_caches
from lib import config, metadata, events


class TestEvents(unittest.TestCase):
    def setUp(self):
        self.tmp = make_tmp_workbench()
        reset_caches()
        self.cfg = config.load(self.tmp)
        self.run_id = "2026-05-18-test"
        metadata.create(
            self.cfg, self.run_id,
            repo_mode="existing", repo_path="/tmp/x", repo_name="x",
            base_ref="HEAD", worktree_name="x", branch_name="agent/x",
            raw_idea_path="raw-idea.md",
        )
        self.actor = {"type": "agent", "name": "test"}

    def tearDown(self):
        cleanup(self.tmp)

    def test_append_valid_event(self):
        ev = events.append(
            self.cfg, self.run_id, "RunCreated",
            payload={
                "raw_idea_path": "raw-idea.md",
                "repo_path": "/tmp/x",
                "repo_name": "x",
                "repo_mode": "existing",
                "worktree_name": "x",
                "branch_name": "agent/x",
            },
            actor=self.actor,
        )
        self.assertEqual(ev["seq"], 1)
        self.assertEqual(ev["type"], "RunCreated")
        self.assertEqual(ev["status"], "draft")
        self.assertTrue(ev["event_id"].startswith("evt_"))

    def test_seq_increments(self):
        for _ in range(3):
            events.append(
                self.cfg, self.run_id, "ArtifactWritten",
                payload={"artifact_key": "x", "path": "x.md"},
                actor=self.actor,
            )
        all_events = list(events.iter_events(self.cfg, self.run_id))
        self.assertEqual([e["seq"] for e in all_events], [1, 2, 3])

    def test_rejects_missing_payload_field(self):
        with self.assertRaises(events.EventError):
            events.append(
                self.cfg, self.run_id, "RunCreated",
                payload={"repo_path": "/tmp/x"},  # missing raw_idea_path, repo_name, etc.
                actor=self.actor,
            )

    def test_rejects_unknown_event_type(self):
        with self.assertRaises(events.EventError):
            events.append(
                self.cfg, self.run_id, "MadeUpEvent",
                payload={},
                actor=self.actor,
            )

    def test_rejects_bad_actor(self):
        with self.assertRaises(events.EventError):
            events.append(
                self.cfg, self.run_id, "ArtifactWritten",
                payload={"artifact_key": "x", "path": "x.md"},
                actor={"type": "unknown_role", "name": "x"},
            )
        with self.assertRaises(events.EventError):
            events.append(
                self.cfg, self.run_id, "ArtifactWritten",
                payload={"artifact_key": "x", "path": "x.md"},
                actor={"name": "x"},  # missing type
            )


if __name__ == "__main__":
    unittest.main()
