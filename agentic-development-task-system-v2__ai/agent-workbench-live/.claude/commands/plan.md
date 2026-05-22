---
description: Run an Agent Workbench planning pass against the target repo. Writes plan.md, preflight.md, assumptions.md, decisions.md. Use when a run is in planning.
---

# /plan

Context: `@context/meta/repo-discovery.md`, `@context/meta/risk-and-approval.md`.

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

Wait for the user to approve. They run `/start $RUN_ID`.

## Reference

`docs/lifecycle.md` § `planning`.
