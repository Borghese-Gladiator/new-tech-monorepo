"""Git + worktree manager.

All git invocations use `git -C <repo_path>` — we never `cd`. Subprocesses are
wrapped to surface stderr in raised errors so the caller can write a useful
audit entry.
"""
from __future__ import annotations

import pathlib
import subprocess
from dataclasses import dataclass

from lib.config import Config


class RepoError(Exception):
    pass


@dataclass(frozen=True)
class RunResult:
    returncode: int
    stdout: str
    stderr: str


def _git(repo_path: pathlib.Path | str, *args: str) -> RunResult:
    cmd = ["git", "-C", str(repo_path), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return RunResult(proc.returncode, proc.stdout, proc.stderr)


def _git_strict(repo_path: pathlib.Path | str, *args: str) -> str:
    r = _git(repo_path, *args)
    if r.returncode != 0:
        cmd = " ".join(["git", "-C", str(repo_path), *args])
        raise RepoError(f"git failed: {cmd}\n{r.stderr.strip()}")
    return r.stdout


def is_git_repo(repo_path: pathlib.Path) -> bool:
    if not repo_path.exists():
        return False
    r = _git(repo_path, "rev-parse", "--is-inside-work-tree")
    return r.returncode == 0 and r.stdout.strip() == "true"


def ref_exists(repo_path: pathlib.Path, ref: str) -> bool:
    r = _git(repo_path, "rev-parse", "--verify", "--quiet", ref)
    return r.returncode == 0


def branch_exists(repo_path: pathlib.Path, branch: str) -> bool:
    r = _git(repo_path, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
    return r.returncode == 0


def worktree_exists(worktree_path: pathlib.Path) -> bool:
    return worktree_path.exists()


def verify_existing(repo_path: pathlib.Path, base_ref: str) -> None:
    """Pre-flight checks for an existing repo."""
    if not repo_path.exists():
        raise RepoError(f"repo path does not exist: {repo_path}")
    if not is_git_repo(repo_path):
        raise RepoError(f"not a git repo: {repo_path}")
    if not ref_exists(repo_path, base_ref):
        raise RepoError(f"base ref {base_ref!r} not found in {repo_path}")


def create_new(repo_path: pathlib.Path, *, monorepo_layout: bool = True) -> str:
    """Initialize a new repo at the given path. Returns initial commit SHA.

    For monorepo layout, scaffolds README.md + docs/ + backend/ + frontend/ shells.
    """
    if repo_path.exists() and any(repo_path.iterdir()):
        raise RepoError(f"refusing to init: {repo_path} exists and is not empty")
    repo_path.mkdir(parents=True, exist_ok=True)
    _git_strict(repo_path, "init", "-q", "-b", "main")
    readme = repo_path / "README.md"
    readme.write_text(f"# {repo_path.name}\n\nScaffold created by Agent Workbench.\n")
    if monorepo_layout:
        for sub in ("docs", "backend", "frontend"):
            (repo_path / sub).mkdir(exist_ok=True)
            (repo_path / sub / ".gitkeep").write_text("")
    _git_strict(repo_path, "add", "-A")
    _git_strict(
        repo_path,
        "-c", "user.name=Agent Workbench",
        "-c", "user.email=agent-workbench@local",
        "commit", "-q", "-m", "chore: agent-workbench initial scaffold",
    )
    sha = _git_strict(repo_path, "rev-parse", "HEAD").strip()
    return sha


def create_worktree(
    repo_path: pathlib.Path,
    branch_name: str,
    worktree_path: pathlib.Path,
    base_ref: str,
) -> None:
    if branch_exists(repo_path, branch_name):
        raise RepoError(f"branch {branch_name!r} already exists in {repo_path}")
    if worktree_path.exists():
        raise RepoError(f"worktree path already exists: {worktree_path}")
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _git_strict(
        repo_path,
        "worktree", "add",
        "-b", branch_name,
        str(worktree_path),
        base_ref,
    )


def remove_worktree(repo_path: pathlib.Path, worktree_path: pathlib.Path, *, force: bool = False) -> None:
    args = ["worktree", "remove", str(worktree_path)]
    if force:
        args.insert(2, "--force")
    _git_strict(repo_path, *args)
