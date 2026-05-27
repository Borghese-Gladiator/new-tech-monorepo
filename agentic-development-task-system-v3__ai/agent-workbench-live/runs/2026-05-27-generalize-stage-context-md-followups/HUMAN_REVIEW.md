# Human review — 2026-05-27-generalize-stage-context-md-followups

## Files

- **Brief** — [brief.md](/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/stages/2_shaping/brief.md)
- **Plan** — [plan.md](/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/stages/3_planning/plan.md)
- **Build (diffs + AC coverage)** — [build.md](/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/stages/4_building/build.md)
- **QA report** — [report.md](/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/stages/5_validating/qa/report.md)
- **Review decision** — [review.md](/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/stages/5_validating/review.md)
- **Audit** — [audit.md](/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/audit.md)

## Summary of changes

- 14 file(s) touched:
  - ``agent-workbench-live/lib/shape_context.py` (new, ~80 LOC) — renders `shape-context.md`. Lifts `raw-idea.md` verbatim, `answers.md` if present, the brief.md template skeleton, and the two shaping rules.`
  - ``agent-workbench-live/lib/plan_context.py` (new, ~220 LOC) — renders `plan-context.md`. Lifts the full brief.md, a deterministic repo-map block (top-level dirs + detected languages + build/test commands from canonical manifests), the brief's "Files likely to change" section, worktree metadata, the plan.md template skeleton, and the planning rules. `_detect_repo_map()` is the only meaningful new logic — narrow manifest-file detection (no recursive scanning, no heuristics).`
  - ``agent-workbench-live/lib/followups_context.py` (new, ~140 LOC) — renders `followups-context.md`. Lifts brief's Non-goals, plan's Risks, review's Decision + Findings, qa report's Known issues, build's Deviations from plan, the follow-ups.md schema, and the followups rules.`
  - ``agent-workbench-live/lib/cli/cmd_shape.py` — added `_write_shape_context_artifacts(cfg, run_id, rd)` helper; called from `--init` after template staging. Imports updated to include `lifecycle` and `shape_context`.`
  - ``agent-workbench-live/lib/cli/cmd_plan.py` — added `_write_plan_context_artifacts(cfg, run_id, rd, staged, meta)` helper; called from `--init` after template staging. Imports updated to include `plan_context`.`
  - ``agent-workbench-live/lib/cli/cmd_followups.py` — added `_write_followups_context_artifacts(cfg, run_id, rd)` helper; called from `--init` after the `validating → followups` transition completes. Imports updated to include `followups_context`.`
  - ``agent-workbench-live/.claude/commands/shape.md` — added "Step 2 — read the curated context" pointing at `stages/2_shaping/shape-context.md`; existing steps renumbered to 3 & 4. Step 1 now documents that `--init` writes the curated file.`
  - ``agent-workbench-live/.claude/commands/plan.md` — same pattern: new Step 2 reads `stages/3_planning/plan-context.md`; existing steps renumbered to 3, 4, 5. Step 1 updated.`
  - …and 6 more
- 5 doc(s) touched:
  - ``agent-workbench-live/.claude/commands/shape.md` — added a new Step 2 (read curated context) and renumbered remaining steps.`
  - ``agent-workbench-live/.claude/commands/plan.md` — same.`
  - ``agent-workbench-live/.claude/commands/followups.md` — restructured Step 2 to put the curated read first; pre-existing artifact-by-artifact list deferred to a "reach for these only when needed" note.`
  - ``agentic-development-task-system-v3__ai/docs/lifecycle.md` — added a "Curated entry context" sub-block under the shape, plan, followups stage sections, plus reworded each stage's "Reads" list to prefer the curated file.`
  - ``agentic-development-task-system-v3__ai/docs/TODO.md` — §5 task list updated to mark the three remaining sub-tasks as shipped, plus shipped-date annotations.`

→ Full diff: `/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/stages/4_building/build.md`

## Testing

**Unit tests**

`python -m unittest tests.test_shape_context tests.test_plan_context tests.test_followups_context -v`

```
Full workbench test suite ran from the worktree's `agent-workbench-live/` directory. 443/450 tests pass; the 7 failures are exactly the pre-existing failures documented in `build.md` § Known issues (5 x `test_backfill_base_ref_sha` PYTHONPATH issue + 2 x `test_human_review.TestSnapshotRender` date-sensitive snapshots). No regressions introduced by this run's changes. The focused subset of new tests (`tests.test_shape_context`, `tests.test_plan_context`, `tests.test_followups_context`) passes 55/55 in 0.578s.

- **tests_passed**: 443 / 450 (98.4%)
- **known_issues_count**: 7 (all pre-existing on master; none regressions)
```

✕ tests failed — 0 known issue(s); see report.

**Manual testing**

_None recorded._

Review decision: **approve**.

Full QA report:

`/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-27-generalize-stage-context-md-followups/stages/5_validating/qa/report.md`

## Run timeline

- [15:15:36] SHAPING — entered shaping
- [15:17:21] PLANNING — entered planning
- [15:23:42] PLANNING — assumption ASM-001: `agent-workbench.yaml`'s policies block does NOT carry build/test command information. The brief's assumption that `plan-context.md` would source build/test co…
- [15:23:42] PLANNING — assumption ASM-002: `shape-context.md`'s leverage is real but modest. The primary win is inlining the brief.md template so the agent doesn't context-switch into `templates/`. If p…
- [15:23:42] PLANNING — assumption ASM-003: The `templates/plan.md` template currently includes inline section blocks for `## Preflight` and `## Decisions & assumptions` (the staged-runs convention). Whe…
- [15:23:42] PLANNING — assumption ASM-004: `cmd_followups.py --init` performs the `validating → followups` transition. The `_write_followups_context_artifacts()` call inserts between `_stage_template()`…
- [15:23:42] PLANNING — decision DR-001: `plan-context.md`'s `_detect_repo_map()` detects languages and build/test commands by checking for canonical manifest files at the worktree root only — no recu…
- [15:23:42] PLANNING — decision DR-002: In `cmd_followups.py`, `_write_followups_context_artifacts()` is called BEFORE `transitions.transition()`. The curated file is written at `runs/$RUN_ID/followu…
- [15:23:42] PLANNING — decision DR-003: Each new generator module duplicates `_read()`, `_section()`, `_HEADING_RE`, and (where used) `_collect_id_blocks()` locally. No extraction to a `lib/_context_…
- [15:23:42] PLANNING — decision DR-004: `shape-context.md` is built (per the run's answers.md decision: "Build it for consistency"). Its `## Rules` block emphasizes the cache-discipline win specifica…
- [15:23:42] PLANNING — decision DR-005: The three new `_write_<stage>_context_artifacts()` helpers each accept only the args they need (not a uniform signature). `_write_shape_context_artifacts(cfg, …
- [15:23:42] PLANNING — decision DR-006: Order of work in the build stage: `shape_context.py` → `followups_context.py` → `plan_context.py`. Shape and followups are mechanically simpler (no repo-map lo…
- [15:23:42] READY — entered ready
- [15:24:04] BUILDING — worktree at `/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups` on `agent/generalize-stage-context-md-followups`
- [15:24:04] BUILDING — worktree on `agent/generalize-stage-context-md-followups` at `/Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260527__generalize-stage-context-md-followups`
- [15:37:06] VALIDATING — entered validating
- [17:16:20] VALIDATING — doc claims: 5 unverified
- [17:16:20] VALIDATING — scope creep: 23 unexpected file(s)
- [17:16:20] VALIDATING — review decision: approve
- [17:16:20] VALIDATING — tests_passed=false; known_issues=0
- [17:16:21] FOLLOWUPS — entered followups
- [17:20:56] FOLLOWUPS — 2 follow-up(s) recorded (refactor, tech_debt)
- [17:21:38] FOLLOWUPS — handoff record created
