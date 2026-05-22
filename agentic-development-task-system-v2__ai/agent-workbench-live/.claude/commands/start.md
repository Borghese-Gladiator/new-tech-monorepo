---
description: Approve an Agent Workbench run in the ready state and create the branch + worktree. Use when the user has reviewed the plan and wants implementation to begin.
---

# /start

Thin wrapper around `agent-workbench start`. Transitions `ready -> building`.

## Preconditions

- Run is in state `ready`.
- `brief.md`, `plan.md`, `preflight.md`, `assumptions.md`, `decisions.md` all exist and are non-empty.

## What you need from the user

- The `run_id`.
- `--approved-by <name>` — who's approving (defaults to current user if you ask).

## Run

```bash
agent-workbench start <run_id> --approved-by "$USER"
```

On success the command creates the worktree at `worktrees/<repo_name>/<worktree_name>/` and prints the path. Tell the user that path so they can `cd` into it for implementation.

## Next step

The agent (you, or another) implements inside the worktree. When done, run `/validate <run_id>`.

## Reference

See `docs/lifecycle.md` § `ready` -> `building`.
