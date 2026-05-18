"""Tests for lib/transitions.

Covers every (from, to) pair declared in schemas/transitions.yaml plus rejection
cases: terminal-state transitions, missing evidence, unknown transitions.
"""
from __future__ import annotations

import unittest

from tests._helpers import make_tmp_workbench, cleanup, reset_caches
from lib import config, metadata, events, transitions


ACTOR = {"type": "agent", "name": "test"}


def _evidence_for(from_state: str, to_state: str, run_id: str) -> dict:
    """Minimal valid evidence for each rule in the schema."""
    if (from_state, to_state) == ("draft", "shaping"):
        return {"raw_idea_path": f"runs/{run_id}/raw-idea.md"}
    if (from_state, to_state) == ("shaping", "planning"):
        return {"brief_path": f"runs/{run_id}/brief.md"}
    if (from_state, to_state) == ("planning", "ready"):
        return {
            "plan_path": "p.md", "assumptions_path": "a.md",
            "decisions_path": "d.md", "preflight_path": "pf.md",
            "repo_path": "/tmp/x", "repo_name": "x",
            "worktree_name": "x", "branch_name": "agent/x",
        }
    if (from_state, to_state) == ("ready", "building"):
        return {
            "approved_by": "tim", "repo_path": "/tmp/x", "repo_name": "x",
            "base_ref": "HEAD", "branch_name": "agent/x", "worktree_name": "x",
            "worktree_path": "/tmp/wt", "preflight_path": "pf.md",
        }
    if (from_state, to_state) == ("building", "validating"):
        return {"implementation_summary_path": "i.md", "diff_summary_path": "ds.md"}
    if (from_state, to_state) == ("validating", "human_review"):
        return {
            "review_report_path": "r.md", "qa_report_path": "qa/report.md",
            "audit_path": "audit.md", "handoff_path": "handoff.md",
            "branch_name": "agent/x", "worktree_path": "/tmp/wt",
        }
    if (from_state, to_state) == ("human_review", "done"):
        return {"accepted_by": "tim", "completion_ref": "local-branch:x", "audit_path": "audit.md"}
    if (from_state, to_state) == ("human_review", "building"):
        return {"bounce_reason": "fix it"}
    return {"abandoned_reason": "stop"}  # wildcard


class TestTransitions(unittest.TestCase):
    def setUp(self):
        self.tmp = make_tmp_workbench()
        reset_caches()
        self.cfg = config.load(self.tmp)

    def tearDown(self):
        cleanup(self.tmp)

    def _make_run(self, rid="r"):
        metadata.create(
            self.cfg, rid,
            repo_mode="existing", repo_path="/tmp/x", repo_name="x",
            base_ref="HEAD", worktree_name="x", branch_name="agent/x",
            raw_idea_path="raw-idea.md",
        )
        return rid

    def _advance(self, run_id, *path):
        for to in path:
            meta = metadata.load(self.cfg, run_id)
            ev = _evidence_for(meta["status"], to, run_id)
            transitions.transition(self.cfg, run_id, to, ev, ACTOR)

    def test_full_happy_path(self):
        rid = self._make_run("happy")
        self._advance(rid, "shaping", "planning", "ready", "building", "validating", "human_review", "done")
        self.assertEqual(metadata.load(self.cfg, rid)["status"], "done")

    def test_bounce_loop(self):
        rid = self._make_run("bounce-loop")
        self._advance(rid, "shaping", "planning", "ready", "building", "validating", "human_review")
        self._advance(rid, "building", "validating", "human_review")
        self.assertEqual(metadata.load(self.cfg, rid)["status"], "human_review")

    def test_abandon_from_each_non_terminal(self):
        # for each non-terminal state, build a run that reaches it and abandon.
        paths = {
            "draft": [],
            "shaping": ["shaping"],
            "planning": ["shaping", "planning"],
            "ready": ["shaping", "planning", "ready"],
            "building": ["shaping", "planning", "ready", "building"],
            "validating": ["shaping", "planning", "ready", "building", "validating"],
            "human_review": ["shaping", "planning", "ready", "building", "validating", "human_review"],
        }
        for n, (state, path) in enumerate(paths.items()):
            rid = f"abandon-{n}"
            self._make_run(rid)
            self._advance(rid, *path)
            self.assertEqual(metadata.load(self.cfg, rid)["status"], state)
            transitions.transition(self.cfg, rid, "abandoned",
                                   {"abandoned_reason": "test"}, ACTOR)
            self.assertEqual(metadata.load(self.cfg, rid)["status"], "abandoned")

    def test_terminal_cannot_transition(self):
        rid = self._make_run("terminal")
        transitions.transition(self.cfg, rid, "abandoned",
                               {"abandoned_reason": "x"}, ACTOR)
        with self.assertRaises(transitions.TransitionError):
            transitions.transition(self.cfg, rid, "shaping",
                                   {"raw_idea_path": "x"}, ACTOR)

    def test_missing_evidence_rejected(self):
        rid = self._make_run("missing-ev")
        with self.assertRaises(transitions.TransitionError):
            transitions.transition(self.cfg, rid, "shaping", {}, ACTOR)
        # TransitionRejected event should have been emitted.
        types = [e["type"] for e in events.iter_events(self.cfg, rid)]
        self.assertIn("TransitionRejected", types)

    def test_unknown_transition_rejected(self):
        rid = self._make_run("no-rule")
        with self.assertRaises(transitions.TransitionError):
            transitions.transition(
                self.cfg, rid, "done",
                {"accepted_by": "x", "completion_ref": "y", "audit_path": "z"},
                ACTOR,
            )

    def test_empty_string_evidence_rejected(self):
        rid = self._make_run("empty-str")
        with self.assertRaises(transitions.TransitionError):
            transitions.transition(self.cfg, rid, "shaping",
                                   {"raw_idea_path": "   "}, ACTOR)

    def test_secondary_events_emitted(self):
        # ready -> building should emit TransitionApplied AND WorktreeCreated.
        rid = self._make_run("secondary")
        self._advance(rid, "shaping", "planning", "ready", "building")
        types = [e["type"] for e in events.iter_events(self.cfg, rid)]
        self.assertIn("WorktreeCreated", types)


if __name__ == "__main__":
    unittest.main()
