"""Unit + snapshot tests for lib/cli/_stop_banner.py (TODO §2)."""
from __future__ import annotations

import contextlib
import io
import os
import pathlib
import unittest

from lib.cli._stop_banner import BORDER, print_stop_banner


SNAPSHOTS = pathlib.Path(__file__).resolve().parent / "snapshots"
SAMPLE_RUN_ID = "SAMPLE-RUN-ID"


def _render(state: str, run_id: str = SAMPLE_RUN_ID) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_stop_banner(state, run_id)
    return buf.getvalue()


class TestPrintStopBanner(unittest.TestCase):
    def test_ready_banner_structure(self):
        out = _render("ready")
        self.assertTrue(out.startswith(BORDER + "\n"))
        self.assertTrue(out.rstrip("\n").endswith(BORDER))
        self.assertIn("STOP. State: ready (human-owned).", out)
        self.assertIn(SAMPLE_RUN_ID, out)
        self.assertIn(f"/start {SAMPLE_RUN_ID}", out)
        # Slash-form replaces the shell-form.
        self.assertNotIn("agent-workbench start", out)
        self.assertIn("Next moves (human-triggered, type in a session):", out)

    def test_no_shell_form_in_any_banner(self):
        """Cross-state pin: no banner renders the shell-form `agent-workbench` literal."""
        for state in ("ready", "human_review", "done", "abandoned"):
            out = _render(state)
            self.assertNotIn(
                "agent-workbench ",
                out,
                f"shell-form leaked into {state} banner",
            )

    def test_human_review_banner_structure(self):
        # No-cfg fallback: only the three slash-form Next moves lines are
        # rendered. The full five-section body is exercised in
        # test_stop_banner_human_review_body.py.
        out = _render("human_review")
        self.assertIn("STOP. State: human_review (human-owned).", out)
        self.assertIn(SAMPLE_RUN_ID, out)
        self.assertIn(f"/complete {SAMPLE_RUN_ID}", out)
        self.assertIn(f"/bounce {SAMPLE_RUN_ID}", out)
        self.assertIn(f"/abandon {SAMPLE_RUN_ID}", out)
        # Slash-form replaces the shell-form (TODO §2 acceptance).
        self.assertNotIn("agent-workbench complete", out)
        self.assertNotIn("agent-workbench bounce", out)
        self.assertNotIn("agent-workbench abandon", out)
        self.assertIn("Next moves (human-triggered, type in a session):", out)

    def test_done_banner_structure(self):
        out = _render("done")
        self.assertIn("STOP. State: done (terminal).", out)
        self.assertIn("Terminal state. No further action.", out)
        self.assertNotIn("Next moves", out)
        # Terminal banners do not interpolate the run_id.
        self.assertNotIn(SAMPLE_RUN_ID, out)

    def test_abandoned_banner_structure(self):
        out = _render("abandoned")
        self.assertIn("STOP. State: abandoned (terminal).", out)
        self.assertIn("Terminal state. No further action.", out)
        self.assertNotIn("Next moves", out)
        self.assertNotIn(SAMPLE_RUN_ID, out)

    def test_invalid_state_raises(self):
        with self.assertRaises(ValueError) as cm:
            print_stop_banner("planning", SAMPLE_RUN_ID)
        self.assertIn("planning", str(cm.exception))

    def test_other_invalid_states_raise(self):
        # Spot-check a couple of other lifecycle states that are NOT
        # agent-stopping. Sanity check on the closed-set validation.
        for bad in ("draft", "shaping", "building", "validating", "followups", ""):
            with self.assertRaises(ValueError):
                print_stop_banner(bad, SAMPLE_RUN_ID)

    def test_border_is_60_columns(self):
        # Pin the border width so future edits don't drift it silently.
        self.assertEqual(len(BORDER), 60)
        out = _render("ready")
        for line in (out.splitlines()[0], out.splitlines()[-1]):
            self.assertEqual(line, BORDER)


class TestSnapshots(unittest.TestCase):
    """Exact-format snapshot per landing state. Catches wording drift.

    Set ``WRITE_SNAPSHOTS=1`` to re-baseline; commit only after eyeballing
    the diff.
    """

    def _check_snapshot(self, state: str) -> None:
        rendered = _render(state)
        path = SNAPSHOTS / f"stop_banner_{state}.expected.txt"
        if os.environ.get("WRITE_SNAPSHOTS"):
            path.write_text(rendered)
            return
        self.assertTrue(
            path.exists(),
            f"missing snapshot: {path}; rerun with WRITE_SNAPSHOTS=1 to baseline",
        )
        expected = path.read_text()
        self.assertMultiLineEqual(expected, rendered)

    def test_ready_snapshot(self):
        self._check_snapshot("ready")

    def test_human_review_snapshot(self):
        self._check_snapshot("human_review")

    def test_done_snapshot(self):
        self._check_snapshot("done")

    def test_abandoned_snapshot(self):
        self._check_snapshot("abandoned")


if __name__ == "__main__":
    unittest.main()
