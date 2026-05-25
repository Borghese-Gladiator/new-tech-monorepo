"""Unit tests for the deterministic validate-context.md / blast-radius
generators (pass-2 B2 + B4).
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest

from lib import validate_context


def _git(path: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True, text=True, check=True,
    ).stdout


def _init_repo(d: pathlib.Path) -> str:
    d.mkdir(parents=True, exist_ok=True)
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@e.x")
    _git(d, "config", "user.name", "test")
    (d / "README.md").write_text("# repo\n")
    _git(d, "add", "README.md")
    _git(d, "commit", "-qm", "initial")
    base = _git(d, "rev-parse", "HEAD").strip()
    return base


class TestValidateContextBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="vctx-"))
        # Inputs.
        self.brief = self.tmp / "brief.md"
        self.brief.write_text(
            "# Brief\n\n## Goal\n\nDo the thing.\n\n## Acceptance criteria\n\n- [x] Thing works.\n"
        )
        self.plan = self.tmp / "plan.md"
        self.plan.write_text(
            "# Plan\n\n## Decisions & assumptions\n\n"
            "### DR-001\n- **Decision**: foo\n\n"
            "### ASM-001\n- **Text**: bar\n\n"
            "### DR-002\n- **Decision**: unused\n"
        )
        self.build_md = self.tmp / "build.md"
        self.build_md.write_text(
            "# Build\n\nRefs: DR-001 and ASM-001.\n\n"
            "## Commands run\n\n- `pytest -q`\n\n"
            "## Known issues\n\n- none\n"
        )
        self.qa = self.tmp / "qa-report.md"
        self.qa.write_text("# QA\n\n## Test results\n\n- 100 passed\n")
        # Real worktree with one extra file.
        self.worktree = self.tmp / "wt"
        self.base_ref = _init_repo(self.worktree)
        (self.worktree / "feature.py").write_text("def f():\n    return 1\n")
        _git(self.worktree, "add", "feature.py")
        _git(self.worktree, "commit", "-qm", "add feature")

    def test_renders_all_sections(self):
        body = validate_context.build(
            brief_path=self.brief,
            plan_path=self.plan,
            build_md_path=self.build_md,
            qa_report_path=self.qa,
            worktree_path=str(self.worktree),
            base_ref=self.base_ref,
        )
        for header in (
            "## Original task",
            "## Acceptance criteria",
            "## Plan decisions + assumptions (filtered)",
            "## Final diff",
            "## Files changed",
            "## Commands run",
            "## Test results",
            "## Known issues / risks",
            "## Reviewer reading order",
        ):
            self.assertIn(header, body, f"missing section: {header}")

    def test_plan_filter_keeps_only_referenced_ids(self):
        body = validate_context.build(
            brief_path=self.brief,
            plan_path=self.plan,
            build_md_path=self.build_md,
            qa_report_path=self.qa,
            worktree_path=str(self.worktree),
            base_ref=self.base_ref,
        )
        self.assertIn("DR-001", body)
        self.assertIn("ASM-001", body)
        # DR-002 is in plan but NOT referenced by build_md — must be filtered.
        self.assertNotIn("DR-002", body)

    def test_plan_filter_fallback_when_no_references(self):
        # Build.md mentions nothing → all IDs should be included.
        (self.tmp / "build-empty.md").write_text("# Build\n\nNothing of note.\n")
        body = validate_context.build(
            brief_path=self.brief,
            plan_path=self.plan,
            build_md_path=self.tmp / "build-empty.md",
            qa_report_path=self.qa,
            worktree_path=str(self.worktree),
            base_ref=self.base_ref,
        )
        self.assertIn("DR-001", body)
        self.assertIn("DR-002", body)

    def test_diff_section_includes_stat(self):
        body = validate_context.build(
            brief_path=self.brief,
            plan_path=self.plan,
            build_md_path=self.build_md,
            qa_report_path=self.qa,
            worktree_path=str(self.worktree),
            base_ref=self.base_ref,
        )
        # Diff stat output mentions the new file.
        self.assertIn("feature.py", body)

    def test_handles_missing_inputs(self):
        body = validate_context.build(
            brief_path=self.tmp / "no-brief.md",
            plan_path=self.tmp / "no-plan.md",
            build_md_path=self.tmp / "no-build.md",
            qa_report_path=self.tmp / "no-qa.md",
            worktree_path=str(self.worktree),
            base_ref=self.base_ref,
        )
        # Generator must not crash; sections should mark themselves as missing.
        self.assertIn("brief.md missing or empty", body)
        self.assertIn("plan.md missing or empty", body)

    def test_write_creates_parent_dir(self):
        target = self.tmp / "deep" / "nested" / "validate-context.md"
        validate_context.write(target, "hello\n")
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), "hello\n")


class TestBlastRadiusBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="blast-"))
        self.worktree = self.tmp / "wt"
        self.base_ref = _init_repo(self.worktree)

    def test_empty_diff(self):
        out = validate_context.build_blast_radius(
            worktree_path=str(self.worktree),
            base_ref=self.base_ref,
        )
        self.assertIn("no files changed", out)

    def test_simple_diff_renders_depth_1(self):
        (self.worktree / "feature.py").write_text(
            "def alpha():\n    return 1\n\n"
            "class Beta:\n    pass\n"
        )
        _git(self.worktree, "add", "feature.py")
        _git(self.worktree, "commit", "-qm", "add")
        out = validate_context.build_blast_radius(
            worktree_path=str(self.worktree),
            base_ref=self.base_ref,
        )
        self.assertIn("depth 1 (changed files):", out)
        self.assertIn("feature.py", out)

    def test_missing_worktree(self):
        out = validate_context.build_blast_radius(
            worktree_path="/nonexistent/path",
            base_ref=self.base_ref,
        )
        self.assertIn("not available", out)


if __name__ == "__main__":
    unittest.main()
