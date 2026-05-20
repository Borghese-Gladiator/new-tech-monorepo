"""Unit tests for lib/doc_claims.py (TODO §1d)."""
from __future__ import annotations

import unittest

from tests._helpers import make_tmp_workbench, cleanup  # noqa: F401

from lib import doc_claims


SECTION_WITH_BULLETS = """\
# Build

## Files changed

- foo.py
- bar.py

## Documentation touched

- README.md — added a /hello example
- docs/api.md: documented the response schema
- AGENTS.md — noted the new dependency

## Commands run

- pytest
"""

SECTION_NONE_NEEDED = """\
# Build

## Documentation touched

none needed — change is internal-only with no user-facing surface

## Commands run
"""

SECTION_ABSENT = """\
# Build

## Files changed

- foo.py

## Commands run
"""

SECTION_EMPTY_BODY = """\
# Build

## Documentation touched

<!-- placeholder hint comment -->

## Commands run
"""


class TestExtract(unittest.TestCase):
    def test_extract_three_bulleted_paths(self):
        out = doc_claims.extract(SECTION_WITH_BULLETS)
        self.assertEqual(out, ["README.md", "docs/api.md", "AGENTS.md"])

    def test_extract_none_needed(self):
        out = doc_claims.extract(SECTION_NONE_NEEDED)
        self.assertIs(out, doc_claims.NONE_NEEDED)

    def test_extract_absent_section_returns_empty(self):
        self.assertEqual(doc_claims.extract(SECTION_ABSENT), [])

    def test_extract_empty_body_returns_empty(self):
        # Only an HTML comment in the section -> no claims, not none-needed.
        self.assertEqual(doc_claims.extract(SECTION_EMPTY_BODY), [])

    def test_extract_skips_template_placeholders(self):
        text = (
            "## Documentation touched\n\n"
            "- <repo-relative path> — example placeholder\n"
            "- (real-doc.md) — another placeholder shape\n"
            "- actual.md — claimed update\n"
        )
        out = doc_claims.extract(text)
        self.assertEqual(out, ["actual.md"])

    def test_case_insensitive_heading(self):
        text = "## documentation Touched\n\n- foo.md — bar\n"
        self.assertEqual(doc_claims.extract(text), ["foo.md"])


class TestVerify(unittest.TestCase):
    """verify() shells out to git, so a real git repo is set up per test."""

    def setUp(self):
        import pathlib
        import subprocess
        import tempfile

        self.repo = pathlib.Path(tempfile.mkdtemp(prefix="aw-doc-"))
        subprocess.run(["git", "-C", str(self.repo), "init", "-q", "-b", "main"], check=True)
        (self.repo / "README.md").write_text("# repo\n")
        (self.repo / "src.py").write_text("x = 1\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        subprocess.run([
            "git", "-C", str(self.repo),
            "-c", "user.name=t", "-c", "user.email=t@x",
            "commit", "-q", "-m", "init",
        ], check=True)
        # New branch with one changed file (src.py), README untouched.
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "feat"], check=True)
        (self.repo / "src.py").write_text("x = 2\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        subprocess.run([
            "git", "-C", str(self.repo),
            "-c", "user.name=t", "-c", "user.email=t@x",
            "commit", "-q", "-m", "change",
        ], check=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_verify_flags_unchanged_claim(self):
        unverified = doc_claims.verify(["README.md", "src.py"], self.repo, "main")
        self.assertEqual(unverified, ["README.md"])

    def test_verify_empty_when_all_claims_changed(self):
        unverified = doc_claims.verify(["src.py"], self.repo, "main")
        self.assertEqual(unverified, [])

    def test_verify_empty_input_returns_empty(self):
        self.assertEqual(doc_claims.verify([], self.repo, "main"), [])

    def test_verify_inconclusive_on_bad_ref(self):
        # Bad ref -> git exits non-zero -> verify returns [] (inconclusive).
        self.assertEqual(doc_claims.verify(["x.md"], self.repo, "no-such-ref"), [])


if __name__ == "__main__":
    unittest.main()
