"""Slug, run_id, branch, and worktree naming.

The templates live in agent-workbench.yaml.defaults, but the rules here are simple:
- run_id  := YYYY-MM-DD-<slug>
- worktree_name := <slug>  (unless caller overrides)
- branch_name   := <branch_prefix>/<worktree_name>
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata

from lib.config import Config


SLUG_MAX_LEN = 60


class NamingError(ValueError):
    pass


def slugify(text: str) -> str:
    """Lowercase kebab-case ASCII slug, length-capped, non-empty."""
    if not text:
        raise NamingError("empty slug input")
    # Normalize unicode -> ascii.
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    norm = norm.lower()
    # Replace non-alphanumeric runs with single hyphen.
    norm = re.sub(r"[^a-z0-9]+", "-", norm)
    norm = norm.strip("-")
    if not norm:
        raise NamingError(f"slug became empty after sanitization: {text!r}")
    if len(norm) > SLUG_MAX_LEN:
        norm = norm[:SLUG_MAX_LEN].rstrip("-") or norm[:SLUG_MAX_LEN]
    return norm


def make_run_id(slug: str, today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    return f"{today.isoformat()}-{slug}"


def make_branch_name(cfg: Config, worktree_name: str) -> str:
    prefix = cfg.defaults.branch_prefix
    return f"{prefix}/{worktree_name}"


def derive_repo_name(repo_path_basename: str) -> str:
    """Default repo name = basename of repo path; sanitize the same way as slugs."""
    return slugify(repo_path_basename)


def make_worktree_path(cfg: Config, repo_name: str, worktree_name: str):
    return cfg.worktrees_path / repo_name / worktree_name
