---
description: Run an Agent Workbench validation pass. Self-review + QA + audit + handoff. Use when a run is in building and the implementation is complete enough for review.
---

# /validate

LLM-bearing. Self-reviews the worktree, runs QA, renders the audit, writes the handoff, then advances `building -> validating -> human_review`.

## Step 1 — stage templates and start validating

```bash
agent-workbench validate "$RUN_ID" --init
```

That:
- transitions `building -> validating`
- stages `implementation-summary.md`, `diff-summary.md`, `review.md`, `qa/report.md`, `handoff.md`
- creates `qa/{artifacts,recordings,traces}/` and `qa/commands.txt`

## Step 2 — write implementation-summary.md and diff-summary.md

Inspect the worktree (`runs/$RUN_ID/metadata.yaml` `target.worktree.path`).

Run from inside the worktree:

```bash
git status
git diff --stat
git log --oneline
```

Fill `implementation-summary.md`: what changed, files changed, acceptance criteria coverage (map to brief.md), deviations from plan, known issues, commands run.

Fill `diff-summary.md`: scope, files added/modified/deleted, highlights for reviewers.

## Step 3 — review

Be adversarial. The reviewer is not the builder. Read `brief.md`, `plan.md`, and the diff, and answer:

- Did the implementation satisfy the brief?
- Did it accidentally expand scope?
- Are there fragile assumptions?
- Missing tests?
- Security / data loss / migration risks?
- What should the human review first?

Write `review.md` with a Decision (`approve` | `request_changes` | `block`) and any findings.

## Step 4 — QA

Pick QA passes appropriate for the repo (any of):

- unit tests
- integration tests
- lint / typecheck
- Playwright (MCP or direct)
- smoke scripts

For each command, append it to `qa/commands.txt` (one per line) and put outputs/screenshots in `qa/artifacts/` or `qa/recordings/`.

Write `qa/report.md` summarizing results: what ran, what passed, what failed, what was not tested.

## Step 5 — handoff

Write `handoff.md`. Keep it short:

- branch + worktree paths
- what was built
- what works
- what doesn't / known issues
- a short ordered list of things the human should check first

## Step 6 — finalize the transition

```bash
agent-workbench validate "$RUN_ID" --tests-passed true --known-issues 0
```

That:
- emits `ReviewCompleted` (decision parsed from `review.md`)
- emits `QACompleted`
- renders `audit.md` from events + artifacts
- emits `AuditRendered` and `HumanHandoffCreated`
- transitions `validating -> human_review`
- prints branch, worktree, audit path

## Next step

Tell the user: the run is in `human_review`. They can `/complete`, `/bounce`, or `/abandon`.

## Reference

`docs/lifecycle.md` § `validating` and § `human_review`.
