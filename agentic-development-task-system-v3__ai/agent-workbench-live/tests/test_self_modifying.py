"""Self-modifying runs: workbench is inside the target repo. TODO §1A + §1C1.

When the workbench IS the target repo's content, the run dir lives inside
the worktree (not in master's working tree). This module proves the
master-stays-clean property end to end.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests._helpers import cleanup, reset_caches  # noqa: F401


ROOT = pathlib.Path(__file__).resolve().parent.parent  # agent-workbench-live/
CLI = ROOT / "bin" / "agent-workbench"


def _make_self_modifying_workbench() -> pathlib.Path:
    """Return a tmp dir that is BOTH a git repo AND a copy of the workbench."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="aw-self-mod-"))
    # Copy bin/, lib/, agent-workbench.yaml, schemas/, templates/ in.
    for name in ("bin", "lib", "schemas", "templates"):
        shutil.copytree(ROOT / name, tmp / name)
    shutil.copy(ROOT / "agent-workbench.yaml", tmp / "agent-workbench.yaml")
    # Initialize as a git repo with an initial commit.
    subprocess.run(["git", "-C", str(tmp), "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    subprocess.run([
        "git", "-C", str(tmp),
        "-c", "user.name=test", "-c", "user.email=test@x",
        "commit", "-q", "-m", "init",
    ], check=True)
    return tmp


def _git_status_porcelain(repo: pathlib.Path) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    )
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def _cli(workbench_root: pathlib.Path, *args, input_text: str | None = None):
    env = os.environ.copy()
    env["AGENT_WORKBENCH_ROOT"] = str(workbench_root)
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(workbench_root), *args],
        capture_output=True, text=True, env=env, input=input_text,
    )


class TestSelfModifyingNewRun(unittest.TestCase):
    """The bug this run fixes: master's tree stays clean of runs/ at new-run."""

    def setUp(self):
        self.tmp = _make_self_modifying_workbench()

    def tearDown(self):
        reset_caches()
        cleanup(self.tmp)

    def test_new_run_creates_worktree_and_clean_master(self):
        idea = self.tmp / "raw-idea.md"
        idea.write_text("# Test self-modifying run\n\nDo a thing.\n")
        r = _cli(
            self.tmp, "new-run",
            "--repo-path", str(self.tmp),
            "--worktree-name", "self-mod-smoke",
            "--base-ref", "main",
            "--idea-file", str(idea),
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        run_id = r.stdout.strip()

        # Master must be clean of runs/ untracked entries (the bug).
        dirty = _git_status_porcelain(self.tmp)
        # Some untracked entries are fine (raw-idea.md at tmp root, plus
        # configured worktrees dir if it lives inside tmp). The key
        # assertion is: NO `agent-workbench-live/runs/` or `runs/` entry.
        for line in dirty:
            self.assertFalse(
                "runs/" in line and run_id in line,
                msg=f"orphan run dir in master tree: {line}",
            )

        # The run dir lives inside the worktree.
        from lib import yaml_io
        # find the worktree from `git worktree list`
        worktrees_out = subprocess.run(
            ["git", "-C", str(self.tmp), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=True,
        ).stdout
        wt_paths = [
            line.split(" ", 1)[1]
            for line in worktrees_out.splitlines()
            if line.startswith("worktree ") and not line.endswith(str(self.tmp))
        ]
        self.assertEqual(len(wt_paths), 1, msg=f"unexpected worktrees: {worktrees_out}")
        wt = pathlib.Path(wt_paths[0])

        run_dir_in_wt = wt / "runs" / run_id
        self.assertTrue(
            (run_dir_in_wt / "metadata.yaml").exists(),
            msg=f"run dir not found inside worktree: {run_dir_in_wt}",
        )
        meta = yaml_io.loads((run_dir_in_wt / "metadata.yaml").read_text())
        self.assertEqual(meta["target"]["worktree"]["path"], str(wt))
        self.assertTrue(meta["target"]["worktree"]["created"])
        self.assertEqual(meta["status"], "draft")


if __name__ == "__main__":
    unittest.main()
