"""Unit tests for lib.metrics.lines."""
from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest

from lib.metrics import lines


def _git(cwd: pathlib.Path, *args, check=True):
    proc = subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@x", *args],
        capture_output=True, text=True, check=check,
    )
    return proc


class TestExtractSha(unittest.TestCase):
    def test_plain_hex(self):
        self.assertEqual(lines._extract_sha("abc1234"), "abc1234")

    def test_local_branch_prefix(self):
        self.assertIsNone(lines._extract_sha("local-branch:agent/x"))

    def test_colon_suffix_sha(self):
        self.assertEqual(lines._extract_sha("merge:abc1234567"), "abc1234567")

    def test_garbage_returns_none(self):
        self.assertIsNone(lines._extract_sha("not-a-sha"))

    def test_full_40_char_sha(self):
        sha = "a" * 40
        self.assertEqual(lines._extract_sha(sha), sha)


class TestGenerated(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="aw-lines-"))
        _git(self.tmp, "init", "-q", "-b", "main")
        (self.tmp / "a.txt").write_text("hello\n")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-q", "-m", "init")

    def test_generated_lines_from_log(self):
        _git(self.tmp, "checkout", "-q", "-b", "feature")
        (self.tmp / "b.txt").write_text("one\ntwo\nthree\n")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-q", "-m", "add b")
        n = lines.count_generated(
            worktree_path=str(self.tmp),
            base_ref="main",
            events_path=None,
        )
        self.assertEqual(n, 3)

    def test_generated_zero_when_no_commits(self):
        n = lines.count_generated(
            worktree_path=str(self.tmp),
            base_ref="main",
            events_path=None,
        )
        self.assertEqual(n, 0)

    def test_generated_includes_artifact_writes(self):
        events_path = self.tmp / "events.jsonl"
        events_path.write_text(
            json.dumps({"type": "ArtifactWritten", "payload": {"content_length_lines": 12}}) + "\n"
            + json.dumps({"type": "ArtifactWritten", "payload": {"content_length_lines": 8}}) + "\n"
            + json.dumps({"type": "Other"}) + "\n"
        )
        n = lines.count_generated(
            worktree_path=str(self.tmp),
            base_ref="main",
            events_path=events_path,
        )
        self.assertEqual(n, 20)


class TestAccepted(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="aw-lines-"))
        _git(self.tmp, "init", "-q", "-b", "main")
        (self.tmp / "a.txt").write_text("hello\n")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-q", "-m", "init")

    def test_accepted_zero_when_no_merge(self):
        n, sha = lines.count_accepted(
            worktree_path=str(self.tmp),
            base_ref="main",
            completion_ref="local-branch:agent/x",
        )
        self.assertEqual(n, 0)
        self.assertIsNone(sha)

    def test_accepted_zero_when_completion_ref_empty(self):
        n, sha = lines.count_accepted(
            worktree_path=str(self.tmp),
            base_ref="main",
            completion_ref=None,
        )
        self.assertEqual(n, 0)
        self.assertIsNone(sha)

    def test_accepted_from_merged_commit(self):
        _git(self.tmp, "checkout", "-q", "-b", "feature")
        (self.tmp / "b.txt").write_text("one\ntwo\n")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-q", "-m", "add b")
        sha = _git(self.tmp, "rev-parse", "HEAD").stdout.strip()
        n, returned_sha = lines.count_accepted(
            worktree_path=str(self.tmp),
            base_ref="main",
            completion_ref=sha,
        )
        self.assertEqual(n, 2)
        self.assertEqual(returned_sha, sha)


if __name__ == "__main__":
    unittest.main()
