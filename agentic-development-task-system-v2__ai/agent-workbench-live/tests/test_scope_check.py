"""Unit tests for lib/scope_check.py (TODO §1g)."""
from __future__ import annotations

import unittest

from tests._helpers import make_tmp_workbench, cleanup  # noqa: F401

from lib import scope_check


BRIEF_WITH_LIKELY = """\
# Brief

## Goal

Add a /hello endpoint.

## Files likely to change

- src/server.py
- src/routes/
- *.md
- tests/test_hello.py

## Acceptance criteria

- Endpoint returns 200.
"""

BRIEF_WITH_SCOPE_HEADING = """\
# Brief

## Scope

- src/foo.py
"""

BRIEF_NO_SECTION = """\
# Brief

## Goal

Just a goal.

## Acceptance criteria

- A
"""

BRIEF_EMPTY_SECTION = """\
# Brief

## Files likely to change

<!-- placeholder; the planner left this empty -->

## Goal

x
"""


class TestExtractExpectedFiles(unittest.TestCase):
    def test_returns_none_when_no_section(self):
        self.assertIsNone(scope_check.extract_expected_files(BRIEF_NO_SECTION))

    def test_returns_empty_for_empty_section(self):
        out = scope_check.extract_expected_files(BRIEF_EMPTY_SECTION)
        self.assertEqual(out, [])

    def test_returns_paths_under_files_likely_to_change(self):
        out = scope_check.extract_expected_files(BRIEF_WITH_LIKELY)
        self.assertEqual(
            out, ["src/server.py", "src/routes/", "*.md", "tests/test_hello.py"]
        )

    def test_accepts_scope_heading(self):
        out = scope_check.extract_expected_files(BRIEF_WITH_SCOPE_HEADING)
        self.assertEqual(out, ["src/foo.py"])

    def test_case_insensitive_heading(self):
        text = "## files Likely to change\n\n- foo.py\n"
        self.assertEqual(scope_check.extract_expected_files(text), ["foo.py"])

    def test_skips_html_comment_placeholders(self):
        text = (
            "## Files likely to change\n\n"
            "<!-- - <placeholder> — describe -->\n"
            "- real.py\n"
        )
        self.assertEqual(scope_check.extract_expected_files(text), ["real.py"])


class TestDetectCreep(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(
            scope_check.detect_creep(["foo.py"], ["foo.py"]), []
        )

    def test_finds_unexpected(self):
        creep = scope_check.detect_creep(["foo.py"], ["foo.py", "bar.py"])
        self.assertEqual(creep, ["bar.py"])

    def test_prefix_match(self):
        creep = scope_check.detect_creep(
            ["src/routes/"], ["src/routes/hello.py", "src/routes/auth.py"]
        )
        self.assertEqual(creep, [])

    def test_prefix_match_does_not_match_unrelated(self):
        creep = scope_check.detect_creep(
            ["src/routes/"], ["src/server.py"]
        )
        self.assertEqual(creep, ["src/server.py"])

    def test_glob_match_extension(self):
        creep = scope_check.detect_creep(
            ["*.md"], ["README.md", "src/foo.py"]
        )
        self.assertEqual(creep, ["src/foo.py"])

    def test_empty_expected_means_all_actual_creep(self):
        creep = scope_check.detect_creep([], ["a.py", "b.py"])
        self.assertEqual(creep, ["a.py", "b.py"])

    def test_no_actual_means_no_creep(self):
        self.assertEqual(scope_check.detect_creep(["a.py"], []), [])


if __name__ == "__main__":
    unittest.main()
