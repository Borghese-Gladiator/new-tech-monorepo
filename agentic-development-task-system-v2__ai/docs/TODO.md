# TODO

## Completed work

- ✅ **Human Review polish** (2026-05-22). Replaced LLM-authored `HUMAN_REVIEW.md` with a code-derived render: clickable absolute-path `## Files` table, code-derived `## Summary of changes` bullets, outcome-only `## Manual testing performed`, and an `events.jsonl`-projected timestamped `## Run timeline`. The `followups -> human_review` transition stdout now carries the absolute path. New module `lib/human_review.py`; wired into `cmd_followups`; required-heading gate updated; snapshot tests added for `happy/` and `bounce_pass2/` fixtures. Commit `623f1af`.
- ✅ **Context Graph** (2026-05-22, merge commit `c635745`). Shipped `agent-workbench-live/context/` — 19 opinionated leaves (README + AUTHORING + git/, languages/{go,javascript-typescript,python}/, infra/, diagnostics/) plus a thin repo-root `CLAUDE.md`. Each leaf carries the four-marker `Applies when:` / `Do:` / `Do not:` / `Commands:` template, fits on one screen (60-line cap test-enforced by `tests/test_context_library.py`), and is indexed in `context/README.md` for `@context/...` lazy imports. Authored on `agent/context-graph` (commits `3214b68` + revert + trim) during run `2026-05-22-context-graph`; landed today as part of TODO §1's orphan-merge cleanup.
- ✅ **Audit unit tests for duplication** (2026-05-22, merge commit `a02dd16`). Folded near-duplicate methods across 10 test modules into `for label, … in cases:` loops (the user's CLAUDE.md "App Testing Rules" pattern), shrinking 193 → 134 tests (−30.6%) with no production code change. Biggest reductions: `test_scope_check.py` 16→2, `test_cmd_board.py` 35→22, `test_doc_claims.py` 10→2. Authored on `agent/audit-unit-tests-for-duplication` (commit `a609d32`) during run `2026-05-22-audit-unit-tests-for-duplication`; landed today as part of TODO §1's orphan-merge cleanup with heading-name fixtures rebased onto v2's polished four-heading set.
- ✅ **Token Efficiency tracking — pass 1** (2026-05-22, merge commit `271ab58`; covered the original TODO §3). Per-run token + cost + acceptance tracking, measurement-only. Shipped 8 metrics modules under `lib/metrics/` (`transcript`/`buckets`/`prices`/`writer`/`lines`/`summary`/`rollup`/`__init__`), `cmd_metrics` CLI with three forms (`<id>`, `--all`, `--rebuild`), hooks at every validate/complete/abandon/followups transition, `metrics/prices.yaml` per-model rate table, board-card metrics band, HUMAN_REVIEW.md `## Token efficiency` block, and 51 tests. Caveat: only `input_tokens` get bucketed — `cache_read` (98.7% of cost on the dogfood run) and `cache_creation` land in `other`, and the slash-command correlator drops every turn into `stage=other` on long sessions. Both are §2 (formerly §4) "pass 2" gaps, not bugs in the pass-1 deliverable. Authored on `agent/token-efficiency-tracking` (commits `9a5a50a`+`d57869e`+`b6178c0`) during run `2026-05-22-token-efficiency-tracking`.
- ✅ **Merge orphan worktree branches** (2026-05-24, merge commits `c635745`+`a02dd16`+`271ab58`; was TODO §1). Closed out the three `status: done` runs whose worktree branches had never been integrated into `202605_agent_workbench_v2` because `cmd_complete` only records a `completion_ref` label, not a merge SHA. Three branches merged in dependency order; the underlying lifecycle gap that allowed this is now TODO §1 (was §2). `agent/poker` deferred — separate-project decision.

---

## 1. Lifecycle gap: `human_review → done` does not merge the worktree branch

Discovered 2026-05-23. Three runs (`2026-05-22-context-graph`, `2026-05-22-audit-unit-tests-for-duplication`, `2026-05-22-token-efficiency-tracking`) reached `status: done` in their `metadata.yaml`, but the work never landed on the parent branch `202605_agent_workbench_v2`. Their deliverables live only on the per-run worktree branches (`agent/context-graph`, etc.) and would have been lost if those worktrees had been deleted on the assumption that "done = merged."

### Root cause

`lib/cli/cmd_complete.py` is the entire implementation of `human_review → done`. It:

1. Writes a `TransitionApplied` event,
2. Records `completion_ref = local-branch:<branch_name>` as a *label* in `metadata.completion`,
3. Prints "done".

It does **not** run `git merge`, `git push`, or touch the worktree. The `completion_ref` is a string, not a merge SHA. So in the current system, "done" means "the human accepted the deliverable on the worktree branch" — the integration back into the parent branch is implicit, unstated, and easy to forget. (The one branch that did land — `agent/human-review-polish` via commit `cd3e5ae` — was merged by hand, not by the lifecycle.)

### Design principles

- **The `done` state must be unambiguous about whether the work is integrated.** Either rename the current "done" to something like `accepted` (with `done` reserved for "accepted AND merged"), or extend `cmd_complete` to perform the merge.
- **The lifecycle should make the merge step impossible to skip silently.** Even if we don't auto-merge, the system should refuse to mark `done` without an explicit merge ref, or surface unmerged-but-done runs loudly on the board.
- **Honest under-attribution over confident mis-attribution** (same principle as token-efficiency tracking): a `completion_ref: local-branch:<branch>` that doesn't claim to be a merge is fine; a `done` state that quietly implies integration is not.

### Options (pick one during implementation)

- **Option A — Auto-merge in `cmd_complete`.** Extend `cmd_complete` to: (a) verify the worktree is clean, (b) check out the parent branch, (c) `git merge --no-ff <worktree_branch>`, (d) record the merge SHA as `completion_ref: merge:<sha>`. Pros: closes the gap completely. Cons: lifecycle now mutates the parent branch — surprising; conflicts during merge would need a recovery story (probably bounce back to a new `merging` state).
- **Option B — Add a `merged` state after `done`.** New `done → merged` transition driven by a new `cmd_merge` subcommand that does the git work. Keep `done` meaning "accepted." Update `agent-workbench list` / board to surface `done` (not `merged`) runs as a "needs integration" bucket. Pros: explicit, conservative. Cons: yet another state for the user to track.
- **Option C — Refuse `done` without a merge ref.** Require `--completion-ref merge:<sha>` (no `local-branch:` default) and have the human run `git merge` first, then call `complete`. The system enforces the order but doesn't do the merge itself. Pros: smallest code change, no new state. Cons: still relies on the human remembering to merge; the friction is just earlier.

Recommend **Option B** — it's the cleanest separation of "human signed off" from "code integrated," and it gives the board something to surface ("3 done runs awaiting merge"). Option A is too magical for what should be a deliberate act.

### Tasks

- [ ] **Pick an option.** Document the choice in `docs/LOG.md` and reflect it in `docs/lifecycle.md` (which currently ends at `done` and would need a new state row for B, or a clarified `done` row for A/C).
- [ ] **Schema change (if Option B).** Add a `merged` status to `schemas/run-metadata.yaml` and the lifecycle state machine in `lib/lifecycle.py` / `lib/transitions.py`. Add a `RunMerged` event type.
- [ ] **Implement `cmd_merge` or extend `cmd_complete`.** Per the chosen option.
- [ ] **Update the board.** `lib/board/snapshot.py` should surface `done`-but-unmerged runs as a distinct card state (Option B) or warn if any `completion_ref` is `local-branch:` rather than `merge:` (Options A/C).
- [ ] **Backfill the three orphan runs.** The 2026-05-24 orphan-merge cleanup landed the work but left `metadata.completion.completion_ref` as `local-branch:<branch>`. Update each to `merge:<sha>` (and `status: merged` under Option B) using the merge SHAs `c635745` / `a02dd16` / `271ab58`. A one-shot script reading `git log --merges` is sufficient.
- [ ] **Tests.** State-machine test for the new transition; CLI smoke test that calling `complete` (Option C) or `merge` (Option B) without the prerequisites fails with a clear error; board test that the new state renders.

### Acceptance

- After a run reaches its terminal state, `metadata.completion.completion_ref` is either a merge SHA or the lifecycle refused the transition.
- `agent-workbench list` or the board makes it impossible to miss a run whose work has been accepted but not merged.
- The three orphan runs (`2026-05-22-context-graph`, `2026-05-22-audit-unit-tests-for-duplication`, `2026-05-22-token-efficiency-tracking`) carry a merge SHA in their metadata after backfill.
- `docs/lifecycle.md` describes the integration step explicitly.

### Non-goals

Auto-push to remote (out of scope; merging is local-only); rewriting `cmd_complete` to handle merge conflicts inline (too risky — if Option A is picked, conflicts bounce to a new state rather than being resolved in-line); changing the meaning of `abandoned` (still a clean terminal that never integrated).

### Origin

Discovered 2026-05-23 during a worktree audit. The user noticed that three runs marked `done` were missing their deliverables from the parent branch; verified by reading `cmd_complete.py` and confirming no git-merge call exists in the lifecycle.

---

## 2. Token efficiency — pass 2: stop bleeding `cache_read`

### Why this is here

Pass 1 shipped per-run metrics, but on its own dogfood run (`runs/2026-05-22-token-efficiency-tracking/metrics.jsonl`) the numbers are:

| Bucket | Tokens | Share | Bucketed by pass 1? |
|---|---:|---:|:---:|
| fresh input | 2,934 | 0.0024% | yes |
| output | 425,478 | 0.34% | n/a |
| cache_creation | 1,178,364 | 0.95% | **no** |
| cache_read | **121,786,040** | **98.7%** | **no** |
| **total** | **123,392,816** | | |
| **cost** | **$236.73** | | |

Pass 1 only buckets `input_tokens`. That accounts for **0.003% of cost**. The renderer literally prints "cache_read not bucketed" (`lib/cli/cmd_metrics.py:88`). So measurement is half-built. Worse: 100% of 621 turns on that run landed in `stage=other, command=""` — the slash-command correlator silently broke, so there isn't even a per-phase split. Both are pass-1 gaps that this section closes.

### Root cause of the 121.8M cache_read

It is the same conversation prefix re-billed every turn:

```
total cache_read ≈ (average prefix size) × (number of turns)
                 ≈ 196,000 × 621
                 ≈ 121.7M
```

Three multiplicative drivers, in priority order of impact:

1. **One long session for build + validate.** 621 turns in one session = a prefix that grows to 295k tokens by the end, re-read on every step. Biggest lever. Mitigation: fresh session at `/validate`.
2. **Validate independently re-reads what the builder already loaded.** `.claude/commands/validate.md` Step 2-3 instructs the model to read `brief.md`, `plan.md`, the diff, and run `git diff` / `git grep` inside the session that already holds the full build history. Every read sticks in the prefix forever after. Mitigation: a single curated `validate-context.md` file.
3. **Per-turn fixed overhead (CLAUDE.md, AGENTS.md, tool defs).** ~10-30k tokens that load every single turn. Even small, multiplied by 621 turns = millions of tokens. Mitigation: audit and shrink.

### Design principles

- **Reduce by structure, not by hiding context.** The validator needs the diff and the right files — not the build session's conversation history. Cut the latter, keep the former.
- **Deterministic context curation > model-curated.** `validate-context.md` is built by Python in `validate --init`, with no LLM call. Cheaper, repeatable, testable.
- **Fresh sessions are first-class lifecycle discipline.** Not "a hint" — call it out in `AGENTS.md`, surface it in CLI output, and make the handoff (`validate-context.md` + run_id + worktree path) explicit. The human still chooses, but the workflow is built around the right default.
- **Attribution before reduction.** Pass 1's bucketer is the only way to know whether mitigations actually worked. Land the cache buckets first; measure the impact of each subsequent task.
- **Honest under-attribution beats confident mis-attribution.** Cache buckets use the same heuristic-and-residual-into-`other` pattern as input buckets.

### Tasks — Part A: visibility (you can't fix what you can't see)

- [ ] **A1. Fix the slash-command correlator.** `lib/metrics/transcript.py:correlate()` + `_cwd_matches()` are landing 100% of turns into `stage=other, command=""` on the pass-1 dogfood run. Diagnose first (suspect: worktree-path resolution vs. `meta.target.worktree.path`, OR `current_command` not propagating across record types). Land a regression test that points at the production transcript's `session_id` and asserts non-empty `stage` distribution. Without this, every per-phase metric is broken.
- [ ] **A2. Bucket `cache_read_input_tokens` and `cache_creation_input_tokens`.** Extend `lib/metrics/buckets.py:attribute()` to return three dicts: existing `input_buckets` plus new `cache_read_buckets` and `cache_creation_buckets`. Computation: walk the transcript prefix per turn (accumulate user/assistant/tool-result text monotonically), apply the existing 4-chars/token heuristic per region, scale to the API's `cache_read_input_tokens` / `cache_creation_input_tokens` counts respectively, residual into `other`. Add the missing buckets: `system_prompt` (constant estimate or first-turn measurement), `tool_defs` (count of tools × ~150 tokens/tool), `repo_files` (tool_results matching the `Read` output gutter pattern `^\s*\d+\t`), `validation_context` (tool_results within a `/validate` span), `generated_drafts` (assistant turns whose body contains markdown headers — proxy for review.md / build.md drafts). Keep `claude_md_and_agents_md`, `context_imports`, `slash_command_body`, `user_messages`, `assistant_history`, `tool_results`, `other`.
- [ ] **A3. Carry session prefix through `correlate()`.** Extend `CorrelatedTurn` with three new tuple fields: `prefix_user_messages`, `prefix_assistant_messages`, `prefix_tool_results`. Unlike the existing `pending_*` per-turn buffers, these accumulate monotonically across the session so A2's bucketer can attribute the cache prefix. Don't clear them on turn boundary.
- [ ] **A4. Surface the new buckets.** Update `RunMetricsSummary` (`lib/metrics/summary.py`) with `cache_read_by_bucket: dict[str, int]` and `cache_creation_by_bucket: dict[str, int]`. Update `_render_summary_plain` (`lib/cli/cmd_metrics.py:88-90`) to drop the "input tokens only" disclaimer and render three sub-sections: `input buckets`, `cache_read buckets`, `cache_creation buckets`.
- [ ] **A5. Per-turn `metrics.jsonl` row update.** `lib/metrics/writer.py:177-199` writes one `bucket_attribution` key today; add `cache_read_attribution` and `cache_creation_attribution` next to it. Bump `schema_version` to 2; summary reader tolerates both.
- [ ] **A6. Cache-miss visibility.** Add `cache_misses: int` to `RunMetricsSummary`, computed as the count of turns where `cache_creation > 1000`. Surface as `cache misses: N` in the per-run summary. Helps detect long pauses that re-wrote the cache (5-minute TTL).
- [ ] **A7. Re-baseline `tokens_per_passing_build`.** Today it's `total_tokens / approves` where `total_tokens` is dominated by `cache_read`, so the metric tracks session length more than agent efficiency. Add `billable_net_per_passing_build = (input + output + cache_creation) / approves` — excluding `cache_read` — alongside. Keep the original for continuity; render both.
- [ ] **A8. Session-turn-count metric.** Add `largest_session_turns: int` and `largest_session_id: str` to `RunMetricsSummary`. Surface in the per-run summary. Required input for A9 and Part B.
- [ ] **A9. Board: session-staleness band.** `lib/board/snapshot.py` already renders a metrics band per pass 1. Append a `turns: N` indicator when `largest_session_turns > 100`. Read-only nudge; no loud-card behavior.

### Tasks — Part B: mitigation (largest impact first)

- [ ] **B1. Promote fresh sessions to a lifecycle discipline in `agent-workbench-live/AGENTS.md`.** Add a `## Session discipline` section. Rules:
  - **Always start a new Claude Code session at the `/validate` boundary** when the building session has > 100 turns. The handoff is the run_id + worktree path; nothing else needs to carry over.
  - **Always start a new session between independent runs.** A new `/new-run` for an unrelated task = exit and relaunch first.
  - **Stay in the same session for `/shape` → `/plan` → `/build`.** These share useful context and the cache amortizes well.
  - **Restart when you see Claude Code's auto-compact notice.** That's a signal you're already paying for a lot of prefix; better to restart than let it compact mid-task.
  - Include the rationale (one paragraph on the prefix-grows-monotonically mechanic; reference the pass-1/pass-2 measurement). Discipline only sticks if the "why" is in front of the reader.
- [ ] **B2. `validate-context.md` template + deterministic auto-generation.** New file at `agent-workbench-live/templates/validate-context.md`. Sections: original task, acceptance criteria, plan decisions + assumptions (load-bearing only — filter for ASM-/DR- IDs referenced in build.md), final diff (`git diff --stat` always; full `git diff` capped at 500 lines, otherwise filenames + per-file line counts), files changed (full list from `git diff --name-status`), commands run (from build.md), test results (from qa/report.md), known issues / risks (from build.md), reviewer reading order (from build.md). `lib/cli/cmd_validate.py:_init` populates the file by reading the run's existing artifacts + running git. Pure Python, deterministic, no LLM call.
- [ ] **B3. Update `/validate` to read `validate-context.md`.** Edit `.claude/commands/validate.md` Step 2-3: replace "Read `brief.md`, `plan.md`, and the diff" with "Read `runs/<id>/stages/5_validating/validate-context.md`. That file is the curated entry point. Read brief/plan/build/qa directly only if validate-context.md points you at a specific section." Add a one-line note that the validator should NOT re-read files that are summarized in validate-context.md.
- [ ] **B4. Pre-compute blast radius.** `templates/review.md` lines 29-54 instruct the model to run `git diff --name-only` + `git grep -n <symbol>` up to depth 3. Move that to Python in `validate --init`: compute the same tree and write `runs/<id>/stages/5_validating/blast-radius.txt`. Update `templates/review.md` to read the file rather than running the commands live. Trades N tool_results for one fixed-size file.
- [ ] **B5. Fresh-session handoff at `validate --init`.** When `validate --init` runs, check `largest_session_turns` for the session that produced `building`. If > 100, print a top-of-output **handoff block** (not just a hint) with the copy-pasteable shape:
  ```
  This run is ready for validation in a fresh Claude Code session.
    run_id:    <id>
    worktree:  <abs path>
    branch:    <branch>
  Exit Claude Code, then:
    cd <worktree>
    claude
    /validate <id>
  The new session bootstraps from validate-context.md — no other context needed.
  ```
  Make the threshold configurable via `agent-workbench.yaml` (`session_staleness_threshold_turns: 100` default).
- [ ] **B6. Audit and shrink CLAUDE.md / AGENTS.md weight.** On a 621-turn session, each 1k tokens of always-loaded instructions costs ~621k tokens of `cache_read`. Read `~/.claude/CLAUDE.md`, repo-root `AGENTS.md`, `agent-workbench-live/AGENTS.md`. For each: identify content that's (a) duplicated across files, (b) only relevant to a specific stage (move into the slash-command body instead — loaded once per invocation), (c) historical/contextual reference that doesn't drive agent behavior (move to docs/architecture.md or LOG.md). Target: cut combined always-loaded instruction weight by 30%+. Land as a single PR with before/after token counts measured via the pass-1 metrics on a same-length dogfood run.
- [ ] **B7. Subagent-first read strategy for `/build` and `/validate`.** Today, file reads happen in the master session and their results stick in the master prefix forever. Update `agent-workbench-live/AGENTS.md` § "Subagent discipline" to require: when a stage needs to read more than 3 files for exploration (not edits), route through an `Explore` subagent. The subagent returns a summary; the master keeps a tiny prefix. Add concrete examples to `.claude/commands/build.md` and `.claude/commands/validate.md`. This is the single most impactful change after fresh sessions — it bounds how big the build session's own prefix can grow.
- [ ] **B8. Tool-output budget guidance.** Add to `agent-workbench-live/AGENTS.md`: a soft budget per Bash tool call (Read outputs > 2k tokens → use `head`/`tail`/grep; `git log` → cap with `-n 20`; `git diff` → `--stat` first, full diff only if needed). Document the pattern so it sticks across sessions. Not enforced — guidance only.

### Tasks — Part C: tests + acceptance gating

- [ ] **C1. Fixture-driven cache-bucket attribution test.** Synthetic transcript with a 100k-token prefix that includes all bucket types in known proportions. Assert `cache_read_by_bucket` attributes correctly within ±2% (the scale step adds rounding noise).
- [ ] **C2. Regression test for the correlator fix.** Load the pass-1 dogfood run's actual transcript via `find_transcripts`. Assert that after the A1 fix, > 50% of turns have non-`other` `stage`.
- [ ] **C3. Snapshot test for `validate-context.md`.** Drive the existing `happy/` and `bounce_pass2/` E2E fixtures through `validate --init`; snapshot the generated file. Catches regressions in the deterministic builder.
- [ ] **C4. CLI smoke test.** `agent-workbench metrics <id>` output includes the three bucket sub-sections, `cache misses: N`, `billable_net_per_passing_build`, and `turns: N`.
- [ ] **C5. End-to-end cost measurement.** After all Part B tasks land, run a `happy/` E2E fixture and measure the new `cache_read` total. Acceptance: total `cache_read` for the run is ≥ 40% lower than the pass-1 dogfood baseline (123.4M → ≤ 74M for an equivalent workload).

### Acceptance

- `agent-workbench metrics <run-id>` prints `cache_read buckets` and `cache_creation buckets` that sum (within ±2%) to the run's `total_cache_read` / `total_cache_creation`.
- On the pass-1 dogfood run, re-running `agent-workbench metrics <id> --record` produces a per-turn `stage` distribution that is no longer 100% `other`.
- `/validate <id>` on a fresh run produces `stages/5_validating/validate-context.md` and `blast-radius.txt` before any LLM call.
- `.claude/commands/validate.md` instructs reading `validate-context.md` instead of brief/plan/build separately.
- `agent-workbench-live/AGENTS.md` has a `## Session discipline` section that names the fresh-session-at-validate rule, the new-session-between-runs rule, and the why.
- `validate --init` prints the full fresh-session handoff block (not just a one-line hint) when `largest_session_turns > 100`.
- `~/.claude/CLAUDE.md` + repo `AGENTS.md` files have measurably-shrunk always-loaded weight (before/after counts in the LOG.md entry).
- `agent-workbench-live/AGENTS.md` § "Subagent discipline" prescribes Explore subagents for multi-file reads in `/build` and `/validate`.
- E2E fixture cache_read drops by ≥ 40% vs. the pass-1 baseline.

### Non-goals

Enforcing cache_read budgets (no hard limits, no warnings that block transitions); auto-restarting Claude Code (no harness automation that exits the user's session); rewriting `lib/metrics/transcript.py` correlator from scratch (it's load-bearing for pass 1 — patch, don't rewrite); cross-session de-duplication of cached prefix (Anthropic's cache layer is what it is — we work around it via session discipline, not at the API layer); supporting non-Claude-Code LLMs.

### How far this gets us — and what it doesn't solve

After this section lands, the answer to "where did the cache_read go" is no longer "unknown." The validate phase's contribution drops materially (curated context + fresh session + pre-computed blast radius). The fixed per-turn overhead drops (CLAUDE.md/AGENTS.md audit). Multi-file exploration stops accumulating in the master prefix (subagent routing).

What pass 2 still doesn't solve and would need future runs:

- **Build-phase compaction.** A `/build` that lasts 200+ turns inside one session still grows its own prefix. Pass 2 mitigates via fresh sessions at the validate boundary, but doesn't address build-mid checkpointing. A future `agent-workbench build --checkpoint` could prompt the model to write `build-progress.md` and recommend a session refresh mid-build.
- **Per-turn cost throttling.** Pass 2 reports per-turn cost but doesn't throttle. Throttling would require either model-side self-summarization or harness-level hard limits — both more invasive than this section's scope.
- **Anthropic-side: auto-compact timing.** Claude Code's auto-compaction isn't aligned to the lifecycle (build → validate boundary). Only Anthropic can change that.

---

## 3. Fix generated_lines for base_ref="HEAD" runs

`lib/metrics/lines.py:count_generated()` runs `git log --numstat <base_ref>..HEAD` to sum `+` lines across the worktree's commit history. The workbench config defaults `base_ref: HEAD` (`agent-workbench.yaml:14`), and `metadata.target.repo.base_ref` is stored as that literal string. The dotted range `HEAD..HEAD` resolves to "no commits" — so `generated_lines` reports 0 for every run that uses the default, regardless of how many commits the builder landed.

Observed on the token-efficiency pass-1 dogfood run: 3 commits with ~2.4k inserted lines across them; `generated_lines: 0`. Same gap will hit every future run that doesn't override `base_ref`.

**Tasks**

- [ ] **Capture a resolved SHA at `/start`.** `lib/cli/cmd_start.py` already calls `git worktree add` — extend the call site to `git rev-parse <base_ref>` first and persist the result. Two options:
  - (a) Add a new field `metadata.target.repo.base_ref_sha` (schema change in `schemas/run-metadata.yaml`).
  - (b) Rewrite `metadata.target.repo.base_ref` in place at `/start` from the literal `"HEAD"` to the resolved SHA. No schema change but loses the "what was the symbolic ref originally" information.
  Prefer (a) — schema is additive, the symbolic ref stays readable.
- [ ] **Prefer the resolved SHA in `lines.py`.** `count_generated()` and `count_accepted()` both take `base_ref`. Update callers to pass `base_ref_sha if present else base_ref`. Add a one-line fallback comment.
- [ ] **Regression test.** `tests/test_metrics_lines.py` already covers `count_generated` via a tmp repo. Add a case that constructs the run-metadata path with `base_ref="HEAD"` and asserts the resolved SHA from `base_ref_sha` produces a non-zero count.
- [ ] **Backfill for existing runs.** Existing `runs/*/metadata.yaml` files don't have `base_ref_sha`. A one-shot script (or a lazy resolver in `lines.py` that calls `git rev-parse` inside the worktree if `base_ref_sha` is missing) handles them. Lazy resolver is simpler — recommended.

**Design principles**

- Don't break the `base_ref: HEAD` config default — many runs are still active against it. The fix is to resolve at use-time (or at start-time), not to forbid the symbolic form.
- Schema changes additive only. No rewrites of existing `metadata.yaml` files.

**Acceptance**

- A new run created with the default `base_ref: HEAD` reports a non-zero `generated_lines` once any commits land on the worktree branch.
- The token-efficiency pass-1 dogfood run (`2026-05-22-token-efficiency-tracking`) reports non-zero `generated_lines` after the lazy resolver lands — either via re-running `metrics --record` on the existing run, or via a one-shot backfill.
- `tests/test_metrics_lines.py` has a regression test that pins the symbolic-ref behavior.

**Non-goals**

Changing the default `base_ref`; making the metrics writer infer the base from `git merge-base`; supporting non-git worktrees.

**Origin**

Discovered during the token-efficiency pass-1 dogfood run (`runs/2026-05-22-token-efficiency-tracking/stages/6_followups/follow-ups.md` § "Fix generated_lines for base_ref=\"HEAD\" runs"). Promoted from per-run follow-up to workbench-level TODO so it's actioned outside the original run.
