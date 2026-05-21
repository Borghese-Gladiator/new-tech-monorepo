---
description: Show all Agent Workbench runs as a Kanban grouped by lifecycle state. Use when the user wants a single-screen view of queue depth and stalled work.
---

# /board

Thin wrapper around `agent-workbench board`.

```bash
agent-workbench board              # active runs only (hides done + abandoned)
agent-workbench board --all        # include done + abandoned
agent-workbench board --status human_review
```

Each card shows `run_id`, age since last update, repo name, and branch. Runs that have been in `human_review` longer than `board.stale_human_review_hours` (default 24h, configurable in `agent-workbench.yaml`) are flagged with `!` and listed in a "Stale human_review" footer.
