"""Unit tests for lib/run_ids.py — slug / run_id / date / worktree helpers."""
from __future__ import annotations

import datetime as dt
import unittest

from lib import run_ids


class TestExtractRunDate(unittest.TestCase):
    def test_happy_paths(self):
        cases = [
            ("2026-05-21-foo", "20260521"),
            ("2026-12-31-some-longer-slug-here", "20261231"),
        ]
        for run_id, expected in cases:
            self.assertEqual(run_ids.extract_run_date(run_id), expected, msg=run_id)

    def test_rejects_bad_inputs(self):
        bad_inputs = [
            "",                       # empty
            "foo-bar-baz",            # no date prefix
            "99-99-99-foo",           # two-digit year, wrong shape
            "not-a-date-foo",         # garbage prefix
            "2026-05-21",             # missing trailing hyphen (bare date isn't a run_id)
        ]
        for bad in bad_inputs:
            with self.assertRaises(run_ids.NamingError, msg=bad):
                run_ids.extract_run_date(bad)


class TestSlugify(unittest.TestCase):
    def test_rejects_empty_or_punctuation(self):
        for bad in ["", "!!!---///"]:
            with self.assertRaises(run_ids.NamingError, msg=bad):
                run_ids.slugify(bad)

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
