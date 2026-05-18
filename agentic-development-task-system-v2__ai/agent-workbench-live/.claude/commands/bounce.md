---
description: Bounce an Agent Workbench run from human_review back to building with a reason. Use when the user wants changes before accepting.
---

# /bounce

Thin wrapper around `agent-workbench bounce`. Transitions `human_review -> building`.

## What you need from the user

- The `run_id`.
- `--reason <text>` — what needs to change.
- `--requested-by <name>`.

## Run

```bash
agent-workbench bounce <run_id> \
  --reason "Game incorrectly allows pair of 4s to beat pair of 7s." \
  --requested-by "$USER"
```

The run goes back to `building`. The original branch and worktree are preserved.

## Reference

See `docs/lifecycle.md` § `human_review` -> `building`.
