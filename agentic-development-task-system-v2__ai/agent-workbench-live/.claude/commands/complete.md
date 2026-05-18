---
description: Accept an Agent Workbench run in human_review and mark it done. Use when the user has reviewed the branch and is satisfied.
---

# /complete

Thin wrapper around `agent-workbench complete`. Transitions `human_review -> done`.

## What you need from the user

- The `run_id`.
- `--accepted-by <name>`.
- Optional `--completion-ref` — defaults to `local-branch:<branch_name>`.

## Run

```bash
agent-workbench complete <run_id> --accepted-by "$USER"
```

## Reference

See `docs/lifecycle.md` § `done`.
