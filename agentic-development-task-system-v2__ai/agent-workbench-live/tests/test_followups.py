"""Unit tests for lib/followups.py (TODO §1f)."""
from __future__ import annotations

import unittest

from tests._helpers import make_tmp_workbench, cleanup  # noqa: F401

from lib import followups


ENTRY = """\
---
title: {title}
motivation: keep it short
suggested_scope: small chunk
category: {category}
---

Optional prose.
"""


def _doc(*entries: str) -> str:
    return "\n".join(entries)


class TestExtract(unittest.TestCase):
    def test_no_blocks_returns_empty(self):
        self.assertEqual(followups.extract_entries("# Follow-ups\n\nNo content.\n"), [])

    def test_one_entry(self):
        out = followups.extract_entries(ENTRY.format(title="a", category="tech_debt"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["title"], "a")
        self.assertEqual(out[0]["category"], "tech_debt")

    def test_multiple_entries(self):
        text = _doc(
            ENTRY.format(title="alpha", category="tech_debt"),
            ENTRY.format(title="beta", category="docs"),
            ENTRY.format(title="gamma", category="bug_risk"),
        )
        out = followups.extract_entries(text)
        self.assertEqual([e["title"] for e in out], ["alpha", "beta", "gamma"])

    def test_categories_helper(self):
        text = _doc(
            ENTRY.format(title="a", category="tech_debt"),
            ENTRY.format(title="b", category="docs"),
            ENTRY.format(title="c", category="tech_debt"),
        )
        cats = followups.categories(followups.extract_entries(text))
        self.assertEqual(cats, ["docs", "tech_debt"])


class TestValidate(unittest.TestCase):
    def test_rejects_empty_file(self):
        errs = followups.validate("")
        self.assertEqual(len(errs), 1)
        self.assertIn("no_followups", errs[0])

    def test_rejects_missing_required_key(self):
        text = "---\ntitle: missing-others\n---\n"
        errs = followups.validate(text)
        self.assertEqual(len(errs), 1)
        self.assertIn("missing required keys", errs[0])

    def test_rejects_invalid_category(self):
        text = ENTRY.format(title="bad", category="not_a_real_category")
        errs = followups.validate(text)
        self.assertEqual(len(errs), 1)
        self.assertIn("invalid category", errs[0])

    def test_rejects_duplicate_titles(self):
        text = _doc(
            ENTRY.format(title="dup", category="docs"),
            ENTRY.format(title="dup", category="bug_risk"),
        )
        errs = followups.validate(text)
        self.assertEqual(len(errs), 1)
        self.assertIn("duplicate", errs[0])

    def test_accepts_no_followups_sentinel(self):
        text = ENTRY.format(title="nothing to surface", category="no_followups")
        self.assertEqual(followups.validate(text), [])

    def test_rejects_sentinel_mixed_with_real_entries(self):
        text = _doc(
            ENTRY.format(title="real", category="tech_debt"),
            ENTRY.format(title="nothing", category="no_followups"),
        )
        errs = followups.validate(text)
        self.assertTrue(any("sentinel" in e for e in errs))

    def test_accepts_all_five_real_categories(self):
        cats = ["tech_debt", "scope_extension", "bug_risk", "refactor", "docs"]
        text = _doc(*(ENTRY.format(title=f"t{i}", category=c) for i, c in enumerate(cats)))
        self.assertEqual(followups.validate(text), [])

    def test_accepts_deferred_from_bounce(self):
        text = ENTRY.format(title="leftover", category="deferred_from_bounce")
        self.assertEqual(followups.validate(text), [])


if __name__ == "__main__":
    unittest.main()
