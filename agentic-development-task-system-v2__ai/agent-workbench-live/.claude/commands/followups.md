---
description: Brainstorm forward-looking candidates for FUTURE runs after a run finishes validating. Writes follow-ups.md; does NOT execute anything. Use when a staged run is in `followups` (validate just transitioned it).
---

# /followups

Context: `@context/meta/risk-and-approval.md`.

LLM-bearing. Reads the just-finished run's artifacts and writes 1–5 forward-looking mini-briefs (or one explicit `no_followups` sentinel) to `follow-ups.md`. **Nothing is executed.** The output is a candidate list for future `/new-run` invocations.

This is a separate stage from `validating` on purpose: validation is backward-looking ("did this run satisfy the brief?"), follow-ups are forward-looking ("what's the next bite worth taking?"). Mixing them biases the review.

## Step 1 — stage the template (only if not already in `followups`)

If `agent-workbench show "$RUN_ID"` reports status `validating`:

```bash
agent-workbench followups "$RUN_ID" --init
```

That transitions `validating -> followups` and stages `follow-ups.md` at the run root. Skip if status is already `followups` (the template lives at `runs/$RUN_ID/follow-ups.md` from a prior `/validate` step's `--init` shortcut, or from a previous `/followups` attempt).

## Step 2 — read the run's outputs

Read (in this order; stop reading once you have enough signal):

1. `runs/$RUN_ID/stages/4_building/build.md` — what was built. Especially the `Known issues`, `Deviations from plan`, and `Files changed` sections.
2. `runs/$RUN_ID/stages/5_validating/review.md` — what the reviewer flagged. Especially blocking findings, scope-creep notes, and (if present) the `Documentation claims` section.
3. `runs/$RUN_ID/stages/5_validating/qa/` — known failures, untested surfaces.
4. `runs/$RUN_ID/stages/3_planning/plan.md` — what was originally scoped, what was deferred.
5. `runs/$RUN_ID/events.jsonl` filtered to `BounceRequested` — items the human explicitly removed from scope via `/bounce`. These are prime candidates for the `deferred_from_bounce` category.
6. `runs/$RUN_ID/archive/2_shaping/brief-v*.md` and `archive/3_planning/plan-v*.md` (if any exist) — earlier versions superseded by a bounce. Items present in v1 but missing from the current canonical files are deferred-from-bounce.

## Step 3 — write follow-ups.md

Replace the template at `runs/$RUN_ID/follow-ups.md` with 1–5 entries. Each entry is a YAML frontmatter block:

```
---
title: <short imperative title>
motivation: <why this matters; reference a concrete pain or risk>
suggested_scope: <one-run-sized chunk; what would be in vs. out>
category: tech_debt | scope_extension | bug_risk | refactor | docs | deferred_from_bounce | no_followups
---

Optional free-form prose explaining the candidate in more depth.
```

Rules:

- **Forward-looking only.** Things to do in a FUTURE run, not corrections to this run.
- **One-run-sized.** Each candidate should be a 1–3 day chunk a single agent could plausibly implement. If it's bigger, split it.
- **Distinguish in-run findings from bounce deferrals.** If something was dropped from scope via `/bounce`, use `category: deferred_from_bounce`. Don't let those silently disappear between briefs.
- **Empty file is INVALID.** If the run genuinely has nothing to surface, write exactly one entry with `category: no_followups` and a motivation explaining the absence (e.g. "Self-contained docs change; no surface for follow-ups.").
- **No duplicates.** Each title must be unique within the file.
- **No execution.** Do not implement any of these. The whole point of this stage is to surface candidates, not act on them.

## Step 4 — finalize the transition

```bash
agent-workbench followups "$RUN_ID"
```

That:

- validates every frontmatter entry (required keys, valid category, no duplicate titles, sentinel-or-real exclusivity)
- emits `FollowupsRecorded` with `{path, entry_count, categories}`
- emits `HumanHandoffCreated`
- transitions `followups -> human_review` (the engine validates `HUMAN_REVIEW.md` carries `## Suggested first checks` and `## Run timeline`)
- moves `follow-ups.md` into `stages/6_followups/`

If validation fails it prints the errors and stops. Fix the file and re-run the command.

## Next step

Tell the user: the run is in `human_review`. They can `/complete`, `/bounce`, or `/abandon`. The `stages/6_followups/follow-ups.md` file is the candidate list for their next bite.

## Reference

`docs/lifecycle.md` § `followups`. TODO §1f.
