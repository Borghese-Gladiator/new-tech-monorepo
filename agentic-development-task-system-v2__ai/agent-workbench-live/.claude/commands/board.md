---
description: Open the live Agent Workbench TUI — a full-screen Kanban over runs/ that auto-refreshes as files change. Use when the user wants an always-on view of what every run is doing right now.
---

# /board

Launches `agent-workbench board` — a Textual TUI that renders every run as a card grouped into a Kanban by lifecycle state. The board re-reads `runs/<id>/metadata.yaml` and `events.jsonl` on every filesystem change (via `watchdog`) plus a 1Hz fallback timer, so the visible state is always what's on disk right now.

```bash
agent-workbench board                     # live TUI; q quits
agent-workbench board --all               # include done + abandoned
agent-workbench board --status building
agent-workbench board --compact           # one-liner cards (narrow terminals)
agent-workbench board --static            # one-shot stdlib-only text dump
```

## Card content (status-aware)

Each card always shows `run_id`, age since `updated_at`, repo, and branch. The body changes by lifecycle state:

- `building` — `build.iterations / max_iterations` with a progress bar; `build.md` presence; "builder gave up" flag if `exit_reason == max_iterations`; recent bounce reason if any.
- `validating` — `tests ✓/✗/?`, `rev ✓/·`, `qa ✓/·`, known-issues count.
- `followups` — entries count (from the latest `FollowupsRecorded` event).
- `human_review` — `! stale <age>` if the run has sat in this state longer than `board.stale_human_review_hours` (default 24h in `agent-workbench.yaml`); bounce count if any.

Every card lists the last 3 events from `events.jsonl` so a moving run is visually moving.

## Loud cards

A card is "loud" (red border + `!` prefix + a `!` marker on its column header) when any of:

- `human_review` and stale.
- `build.exit_reason == max_iterations`.
- `validation.tests_passed == false`.
- `validation.known_issues_count > 0`.
- An `ErrorRecorded` event after the last `TransitionApplied`.

## Requirements

The live board needs `textual` and `watchdog`:

```bash
pip install -r requirements-board.txt
```

If they're missing, `agent-workbench board` exits with an install hint. `agent-workbench board --static` always works (stdlib only) and is the right choice for CI / headless / piping.

## Out of scope

Read-only — `q` quits, no other keystrokes. Mutate state via the lifecycle CLI / slash commands in another pane.
