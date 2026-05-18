"""new-run subcommand."""
from __future__ import annotations

import pathlib
import sys

from lib import metadata, events, run_ids, repos
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Create a new run from a raw idea."


def register(p) -> None:
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--repo-path", type=pathlib.Path, help="Path to an existing git repo.")
    g.add_argument("--new-repo-path", type=pathlib.Path, help="Path where a new repo will be created.")
    p.add_argument("--worktree-name", required=True, help="Slug for the worktree (and default for branch).")
    p.add_argument("--idea-file", type=pathlib.Path, help="File containing the raw idea (else read stdin).")
    p.add_argument("--scope-kind", default="implementation",
                   choices=("implementation", "bootstrap", "roadmap", "research", "repair"))
    p.add_argument("--scope-summary", default="", help="Short one-line summary of the scope.")
    p.add_argument("--repo-name", help="Override repo name (defaults to basename of repo path).")
    p.add_argument("--base-ref", help="Base ref for the worktree (defaults to config).")


def run(args) -> int:
    cfg = load_config(args)

    if args.new_repo_path:
        repo_path = args.new_repo_path.resolve()
        repo_mode = "new"
    else:
        repo_path = args.repo_path.resolve()
        repo_mode = "existing"

    base_ref = args.base_ref or cfg.defaults.base_ref

    # Validate target.
    if repo_mode == "existing":
        try:
            repos.verify_existing(repo_path, base_ref)
        except repos.RepoError as e:
            return fail(str(e), 2)
    else:
        if repo_path.exists() and any(repo_path.iterdir()):
            return fail(f"new repo path is not empty: {repo_path}", 3)

    # Name resolution.
    try:
        worktree_name = run_ids.slugify(args.worktree_name)
    except run_ids.NamingError as e:
        return fail(f"invalid --worktree-name: {e}", 2)
    repo_name = args.repo_name or run_ids.derive_repo_name(repo_path.name)
    branch_name = run_ids.make_branch_name(cfg, worktree_name)

    # Run ID.
    run_id = run_ids.make_run_id(worktree_name)
    if metadata.run_dir(cfg, run_id).exists():
        return fail(f"run id collision: {run_id} already exists", 3)

    # Idea text.
    if args.idea_file:
        if not args.idea_file.exists():
            return fail(f"--idea-file not found: {args.idea_file}", 2)
        idea = args.idea_file.read_text()
    else:
        if sys.stdin.isatty():
            return fail("provide --idea-file or pipe the idea on stdin", 2)
        idea = sys.stdin.read()
    idea = idea.strip()
    if not idea:
        return fail("idea is empty", 2)

    # Create the run.
    metadata.create(
        cfg, run_id,
        repo_mode=repo_mode,
        repo_path=str(repo_path),
        repo_name=repo_name,
        base_ref=base_ref,
        worktree_name=worktree_name,
        branch_name=branch_name,
        raw_idea_path="raw-idea.md",
        scope_kind=args.scope_kind,
        scope_summary=args.scope_summary,
    )
    rd = metadata.run_dir(cfg, run_id)
    (rd / "raw-idea.md").write_text(idea + "\n")

    # For new repos, create now so the path is real before planning.
    initial_sha = None
    if repo_mode == "new":
        try:
            initial_sha = repos.create_new(repo_path, monorepo_layout=True)
        except repos.RepoError as e:
            return fail(f"failed to init new repo: {e}", 2)
        # Update metadata with the SHA.
        def _mutator(d):
            d["target"]["repo"]["fingerprint"] = initial_sha
        metadata.update(cfg, run_id, _mutator)

    actor = actor_from_env("agent")
    events.append(
        cfg, run_id, "RunCreated",
        payload={
            "raw_idea_path": str(rd / "raw-idea.md"),
            "repo_path": str(repo_path),
            "repo_name": repo_name,
            "repo_mode": repo_mode,
            "worktree_name": worktree_name,
            "branch_name": branch_name,
            "base_ref": base_ref,
            "scope_kind": args.scope_kind,
        },
        actor=actor,
    )
    if initial_sha:
        events.append(
            cfg, run_id, "ArtifactWritten",
            payload={"artifact_key": "new_repo", "path": str(repo_path), "summary": f"initial commit {initial_sha[:10]}"},
            actor=actor,
        )

    print(run_id)
    return 0
