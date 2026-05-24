---
description: Accept an Agent Workbench run in human_review and mark it done. Auto-merges the run's worktree branch into the parent branch as part of the transition.
---

# /complete

Thin wrapper around `agent-workbench complete`. Transitions `human_review -> done` AND merges the worktree branch into the parent branch (`--no-ff`).

## Pre-flight (tell the user before invoking)

**This will run `git merge --no-ff <worktree_branch>` against the parent branch in the target repo.** Make sure the worktree is committed; uncommitted changes will block the merge.

## What you need from the user

- The `run_id`.
- `--accepted-by <name>`.

## Run

```bash
agent-workbench complete <run_id> --accepted-by "$USER"
```

On success the CLI prints three lines: the transition (`human_review -> done`), the new `completion_ref` (formatted `merge:<sha>`), and a `merged <branch> into <parent_branch> (<sha-short>)` confirmation.

## Failure modes

- **Dirty worktree.** The worktree at `metadata.target.worktree.path` has uncommitted changes. The CLI refuses with a non-zero exit and the run stays in `human_review`. Commit (or stash) and re-run.
- **Merge conflict.** `git merge --abort` runs cleanly, a `MergeConflict` event is appended to `events.jsonl`, the run stays in `human_review`, and the CLI returns non-zero. Resolve the conflict manually in the parent repo, then re-run `complete`.
- **Detached HEAD / missing branch.** If `base_ref` cannot be resolved to a real branch, the CLI refuses.

## Escape hatches

- `--no-merge` — skip the merge and record `completion_ref: local-branch:<branch_name>` instead. The board will surface the run as `⚠ unmerged` until the merge happens by hand. Use only when the target-repo state makes auto-merging unsafe.
- `--completion-ref <value>` — explicit override; the CLI records the string verbatim and skips the merge.

## Reference

See `docs/lifecycle.md` § `done`. TODO §1 (resolved) tracks the merge work.
