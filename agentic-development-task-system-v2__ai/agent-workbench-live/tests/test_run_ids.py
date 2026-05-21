"""Unit tests for lib/run_ids.py — slug / run_id / date / worktree helpers."""
from __future__ import annotations

import datetime as dt
import unittest

from lib import run_ids


class TestExtractRunDate(unittest.TestCase):
    def test_happy_path(self):
        self.assertEqual(run_ids.extract_run_date("2026-05-21-foo"), "20260521")

    def test_longer_slug(self):
        self.assertEqual(
            run_ids.extract_run_date("2026-12-31-some-longer-slug-here"),
            "20261231",
        )

    def test_empty_string_raises(self):
        with self.assertRaises(run_ids.NamingError):
            run_ids.extract_run_date("")

    def test_missing_date_prefix_raises(self):
        with self.assertRaises(run_ids.NamingError):
            run_ids.extract_run_date("foo-bar-baz")

    def test_malformed_date_prefix_raises(self):
        # Two-digit year — not the YYYY-MM-DD shape the regex requires.
        with self.assertRaises(run_ids.NamingError):
            run_ids.extract_run_date("99-99-99-foo")

    def test_garbage_prefix_raises(self):
        with self.assertRaises(run_ids.NamingError):
            run_ids.extract_run_date("not-a-date-foo")

    def test_no_trailing_hyphen_raises(self):
        # The regex requires the trailing "-" so a bare date isn't a run_id.
        with self.assertRaises(run_ids.NamingError):
            run_ids.extract_run_date("2026-05-21")


class TestSlugify(unittest.TestCase):
    def test_empty_raises(self):
        with self.assertRaises(run_ids.NamingError):
            run_ids.slugify("")

    def test_all_punctuation_raises(self):
        with self.assertRaises(run_ids.NamingError):
            run_ids.slugify("!!!---///")

    def test_lowercase_kebab(self):
        self.assertEqual(run_ids.slugify("Hello World"), "hello-world")

    def test_unicode_stripped(self):
        # The "é" gets folded to "e" by NFKD, "ñ" to "n".
        self.assertEqual(run_ids.slugify("café piña"), "cafe-pina")


class TestMakeRunId(unittest.TestCase):
    def test_uses_provided_date(self):
        rid = run_ids.make_run_id("foo", today=dt.date(2026, 5, 21))
        self.assertEqual(rid, "2026-05-21-foo")
        # And it round-trips through extract_run_date.
        self.assertEqual(run_ids.extract_run_date(rid), "20260521")


if __name__ == "__main__":
    unittest.main()
