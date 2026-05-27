---
description: Run an Agent Workbench planning pass against the target repo. Writes plan.md, preflight.md, assumptions.md, decisions.md. Use when a run is in planning.
---

# /plan

LLM-bearing. Reads `brief.md` and the target repo, writes the four planning artifacts, then advances `planning -> ready`.

## Step 1 — stage templates and verify state

```bash
agent-workbench plan "$RUN_ID" --init
```

That copies `templates/{plan,preflight,assumptions,decisions}.md` into the run dir if missing.

## Step 2 — inspect the target repo

Read `runs/$RUN_ID/brief.md` and the **target repo** identified in `runs/$RUN_ID/metadata.yaml` at `target.repo.path`.

You may spawn `Explore` subagents to map the repo:

- one to find relevant files
- one to map data models or schemas
- one to map the UI surface

The master session collates their findings into `plan.md`. Subagents must not write to the run directory directly.

## Step 3 — write the four artifacts

### `plan.md`
- Current repo understanding
- Relevant files
- Proposed changes
- Files likely to change
- Data model changes
- UI changes
- Test plan
- QA plan
- Risks
- Definition of done

### `preflight.md`
Fill out the repo_path / repo_name / base_ref / branch_name / worktree_name fields and the checks block. Note any warnings.

### `assumptions.md`
Every assumption you made instead of asking the user. Use IDs `ASM-001`, `ASM-002`, … Each needs Text, Reason, Impact.

### `decisions.md`
Every design / implementation decision. Use IDs `DR-001`, `DR-002`, … Each needs Decision, Rationale, Alternatives considered, Why not the alternatives.

**Rules:**
- **Do NOT ask the user questions.** If something is ambiguous, record it as an assumption and choose the safest small implementation.
- If the task is too broad, reduce scope. Note in the plan what was deferred.

## Step 4 — finalize the transition

```bash
agent-workbench plan "$RUN_ID"
```

That:
- verifies all four artifacts are non-empty
- parses `assumptions.md` and `decisions.md` to emit `AssumptionRecorded` / `DecisionRecorded` events
- emits `PreflightCompleted`
- transitions `planning -> ready`

## Next step

Auto-chain: immediately invoke `/start $RUN_ID` once `planning -> ready` has been recorded by the CLI. The CLI still emits a `STOP.` banner on the `planning -> ready` transition for audit purposes, but `ready` is a transient state that the agent passes through — it is no longer an agent-stopping gate. The next (and only) human gate is `human_review`, owned by `/complete`, `/bounce`, and `/abandon`.

Before invoking `/start`, briefly tell the user:

- The `run_id` and that planning is complete.
- The path to `plan.md`.
- A one-paragraph summary of the proposed changes and the top risks.
- That you are now invoking `/start $RUN_ID` to create the worktree and begin implementation.

Then invoke `/start $RUN_ID`. `/start` will obtain `--approved-by` from the current user automatically (no prompt needed on the auto-chain path).

### Stop conditions (do NOT auto-chain)

Stop and hand control back to the user only if:

- The user explicitly told you to stop after `/plan` ("just plan it", "stop after plan", "don't start yet", etc.).
- The CLI returned a warning or non-zero status from `agent-workbench plan`.

## Reference

`docs/lifecycle.md` § `planning`.
