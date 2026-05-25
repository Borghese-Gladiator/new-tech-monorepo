# TODO

## Completed work

- ✅ **Human Review polish** (2026-05-22). Replaced LLM-authored `HUMAN_REVIEW.md` with a code-derived render: clickable absolute-path `## Files` table, code-derived `## Summary of changes` bullets, outcome-only `## Manual testing performed`, and an `events.jsonl`-projected timestamped `## Run timeline`. The `followups -> human_review` transition stdout now carries the absolute path. New module `lib/human_review.py`; wired into `cmd_followups`; required-heading gate updated; snapshot tests added for `happy/` and `bounce_pass2/` fixtures. Commit `623f1af`.
- ✅ **Context Graph** (2026-05-22, merge commit `c635745`). Shipped `agent-workbench-live/context/` — 19 opinionated leaves (README + AUTHORING + git/, languages/{go,javascript-typescript,python}/, infra/, diagnostics/) plus a thin repo-root `CLAUDE.md`. Each leaf carries the four-marker `Applies when:` / `Do:` / `Do not:` / `Commands:` template, fits on one screen (60-line cap test-enforced by `tests/test_context_library.py`), and is indexed in `context/README.md` for `@context/...` lazy imports. Authored on `agent/context-graph` (commits `3214b68` + revert + trim) during run `2026-05-22-context-graph`; landed today as part of TODO §1's orphan-merge cleanup.
- ✅ **Audit unit tests for duplication** (2026-05-22, merge commit `a02dd16`). Folded near-duplicate methods across 10 test modules into `for label, … in cases:` loops (the user's CLAUDE.md "App Testing Rules" pattern), shrinking 193 → 134 tests (−30.6%) with no production code change. Biggest reductions: `test_scope_check.py` 16→2, `test_cmd_board.py` 35→22, `test_doc_claims.py` 10→2. Authored on `agent/audit-unit-tests-for-duplication` (commit `a609d32`) during run `2026-05-22-audit-unit-tests-for-duplication`; landed today as part of TODO §1's orphan-merge cleanup with heading-name fixtures rebased onto v2's polished four-heading set.
- ✅ **Token Efficiency tracking — pass 1** (2026-05-22, merge commit `271ab58`; covered the original TODO §3). Per-run token + cost + acceptance tracking, measurement-only. Shipped 8 metrics modules under `lib/metrics/` (`transcript`/`buckets`/`prices`/`writer`/`lines`/`summary`/`rollup`/`__init__`), `cmd_metrics` CLI with three forms (`<id>`, `--all`, `--rebuild`), hooks at every validate/complete/abandon/followups transition, `metrics/prices.yaml` per-model rate table, board-card metrics band, HUMAN_REVIEW.md `## Token efficiency` block, and 51 tests. Caveat: only `input_tokens` get bucketed — `cache_read` (98.7% of cost on the dogfood run) and `cache_creation` land in `other`, and the slash-command correlator drops every turn into `stage=other` on long sessions. Both are §2 (formerly §4) "pass 2" gaps, not bugs in the pass-1 deliverable. Authored on `agent/token-efficiency-tracking` (commits `9a5a50a`+`d57869e`+`b6178c0`) during run `2026-05-22-token-efficiency-tracking`.
- ✅ **Merge orphan worktree branches** (2026-05-24, merge commits `c635745`+`a02dd16`+`271ab58`; was TODO §1). Closed out the three `status: done` runs whose worktree branches had never been integrated into `202605_agent_workbench_v2` because `cmd_complete` only records a `completion_ref` label, not a merge SHA. Three branches merged in dependency order; the underlying lifecycle gap that allowed this is now TODO §1 (was §2). `agent/poker` deferred — separate-project decision.
- ✅ **Lifecycle gap: `human_review → done` does not merge the worktree branch** (2026-05-24, merge commit `0069070`; was TODO §1, Option A from the choices). `agent-workbench complete` now performs `git merge --no-ff` of the worktree branch into the parent branch as part of the transition; success records `completion_ref: merge:<full-sha>` and emits a new `WorktreeMerged` event; conflict aborts cleanly, emits `MergeConflict`, and leaves the run in `human_review`. Dirty worktree refuses; bad `base_ref` refuses. Backfilled all four pre-existing `local-branch:` runs (the original three orphans plus this run itself, which ran its own first `complete` on the legacy code path because the new code wasn't live yet — full SHAs in `tools/backfill_completion_refs.py`). The board surfaces `⚠ unmerged` on any `done` run whose `completion_ref` still starts with `local-branch:`. Shipped on `agent/auto-merge-on-complete` (commit `5adca50`) during run `2026-05-24-auto-merge-on-complete`; +15 new repos unit tests, +3 new merge E2E tests (dirty-worktree refusal, conflict abort + `MergeConflict` event, `--no-merge` escape hatch), +3 new badge tests; full suite 233/235 (the 2 failures are pre-existing date-baked snapshot drift on master).

---

## 1. Token efficiency — pass 2: stop bleeding `cache_read`

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

## 2. CLI stop banner on agent-stopping transitions

Discovered 2026-05-24 during the auto-merge-on-complete run's retro. The workbench's lifecycle has two stages where the agent does no work — `human_review` (human inspects + decides) and `ready` (human approves the plan) — plus the terminal states `done` and `abandoned`. Today there is no per-state directive file telling the agent "stop here." The agent is expected to read `docs/lifecycle.md` and self-police; the only stop signal in-band is a sentence at the bottom of the *exiting* slash command (e.g. `followups.md` line 73: "Tell the user: the run is in `human_review`."). On the auto-merge dogfood run, the agent (me) drove straight through `human_review` into `complete` without pausing, exactly because nothing in the agent's immediate tool output said "stop." The structural gap is that agent-stopping transitions land silently — the CLI prints `<id>: followups -> human_review` and a path to `HUMAN_REVIEW.md`, but nothing that flags this as a hard handoff.

### Chosen direction

Land a stop banner in the CLI's stdout for any transition that lands in a state the agent does not drive. The banner is printed by the command that performs the transition, immediately after the existing transition line. Implemented in a small new helper (`lib/cli/_stop_banner.py`) so the format stays consistent across commands.

The states this fires for:

| Landing state | Reason | Banner action |
|---|---|---|
| `ready` | Human approves the plan via `/start`. | STOP. Wait for human to `/start`. |
| `human_review` | Human inspects + decides via `/complete`, `/bounce`, `/abandon`. | STOP. Wait for human. |
| `done` | Terminal. | STOP. Run accepted. |
| `abandoned` | Terminal. | STOP. Run abandoned. |

### Design principles

- **The signal lands in the agent's most recent tool output.** That is where the agent's attention is. Docs the agent might have read earlier in the session are unreliable; the banner is unmissable because it's the very last thing printed.
- **Convention over enforcement.** This is a *nudge*, not a hard block. An agent in auto mode that's been explicitly told to drive a run end-to-end can still proceed past it — but the banner makes that an active choice, not an oversight. Hard enforcement (Option 4 / Option 6 from the brainstorm) was rejected as too heavyweight and runtime-coupled.
- **One source of truth for the banner format.** Every command that triggers an agent-stopping transition calls the same helper; the wording stays in sync.
- **Bordered + visually distinct.** Block of `=` characters and the literal word `STOP` so it doesn't blend with normal log lines.

### Tasks

- [ ] **Add `lib/cli/_stop_banner.py`.** One function: `print_stop_banner(landing_state: str, run_id: str, *, next_commands: list[str] | None = None) -> None`. Internal table mapping each of the four landing states to a (reason, next-step text) pair. Format:
  ```
  ============================================================
  STOP. State: <landing_state> (<owner>-owned).
  <one-line explanation>.

  Next moves (<owner>-triggered):
    agent-workbench <cmd> <run_id>    — <one-line description>
    ...
  ============================================================
  ```
  Width capped at 60 columns (matches the existing CLI output style).
- [ ] **Wire the banner into the four commands that perform agent-stopping transitions.** Call `print_stop_banner(landing_state=..., run_id=...)` immediately after the existing transition-success print:
  - `lib/cli/cmd_plan.py` — landing state `ready` (the `planning -> ready` transition).
  - `lib/cli/cmd_validate.py` — landing state `human_review` (the flat-layout `validating -> human_review` path).
  - `lib/cli/cmd_followups.py` — landing state `human_review` (the staged `followups -> human_review` path).
  - `lib/cli/cmd_complete.py` — landing state `done`.
  - `lib/cli/cmd_abandon.py` — landing state `abandoned`.
- [ ] **`AGENTS.md` cross-reference.** Add one sentence in `agent-workbench-live/AGENTS.md` under "How to drive the workbench" pointing at the banner: "When you see a `STOP.` banner in CLI output, your session ends. Do not invoke the listed next commands — those are the human's call."
- [ ] **Tests.**
  - Unit test for `_stop_banner.print_stop_banner`: four states × asserts on the banner text + the next-command list. Use `capsys` / `io.StringIO`.
  - E2E test extension: `TestE2EHappyPath.test_happy_path` already drives through every agent-stopping transition; assert `STOP.` appears in stdout after the `followups` and `complete` calls.
  - Snapshot test for the banner's exact format (one fixture per landing state) so wording drift is caught in PRs.

### Acceptance

- Running `/plan <id>` (when it lands at `ready`), `/validate <id>` (flat-layout), `/followups <id>`, `/complete <id>`, and `/abandon <id>` each prints a STOP banner as the last thing in stdout.
- The banner names the landing state, says who owns it, and lists the exact next commands the human (or no one, for terminals) would invoke.
- The banner is consistent across all four call sites (driven by `_stop_banner.print_stop_banner`).
- `AGENTS.md` cross-references the banner once.
- Tests pin both the trigger points and the exact format.

### Non-goals

Hard enforcement (the agent can still run past the banner — by design, see Design principles above). Hooks-based call interception (out of scope for this task; the workbench is meant to be runtime-agnostic). Banners for transitions that the agent itself drives (`draft -> shaping`, `shaping -> planning`, `ready -> building`, `building -> validating`, `validating -> followups`) — those are agent continuations, not stops, and adding banners there would dilute the signal. Per-state contract files in `docs/states/<state>.md` (a separate idea that was considered and rejected for this task — `docs/lifecycle.md` already carries the state contracts; this task is purely about runtime visibility, not docs reorg).

### Origin

Discovered 2026-05-24 during the retro of run `2026-05-24-auto-merge-on-complete`. The agent driving that run did not stop at `human_review`; it continued straight into `/complete` because nothing in the CLI's most recent stdout marked `human_review` as a hand-off. The user's question — "is there a markdown file for human_review?" — surfaced the asymmetry: every *transition* has a slash-command body, but states the agent doesn't drive have no agent-discoverable signal. Six options were brainstormed (stronger stop language in `followups.md`; per-state contract files in `docs/states/`; CLI stop banner; hooks-based enforcement; agent-action column in `lifecycle.md`'s state table; refuse-from-agent-actor in the transition engine). Option 3 (CLI banner) chosen for its leverage-to-effort ratio: signal lands in the agent's most recent tool output, additive to other future fixes, runtime-agnostic, small surface area.

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

---

## 4. Structured human_review handoff output

Discovered 2026-05-24 while reviewing the CLI's human_review landing output. The `STOP.` banner (§2) lands the agent's attention, but the *content* the banner carries is currently inconsistent across call sites: `cmd_followups.py` prints a terse "Next moves" command list with no summary; `cmd_validate.py` (the dogfood example) prints a hand-typed multi-paragraph block with commit SHA, test counts, and per-artifact links inline. Same lifecycle event, two very different shapes. The agent — and the human reading the agent's tool output — has to re-derive what's load-bearing each time. This task pins a single structured shape.

### Design principles

- **Banner is a pointer + minimum decision info; HUMAN_REVIEW.md is canonical.** The banner exists so the human can decide *whether to open HUMAN_REVIEW.md* (or which of `/complete`/`/bounce`/`/abandon` to type without opening anything). Anything that belongs in HUMAN_REVIEW.md (branch, commit SHA, full file-by-file diff, test result counts, per-artifact links, known issues, run timeline) does NOT belong in the banner. The renderer in `lib/human_review.py` already produces all of that — the banner must not duplicate it.
- **Worktree paths are not memorizable.** Each run lives in a worktree under `~/GitHub/LOCAL_worktrees/...` with a date-and-slug name the human did not pick. The banner MUST print the absolute path to HUMAN_REVIEW.md so the human can open it without re-deriving the worktree directory.
- **Decision text, not commands.** The "next moves" lines are reminders, not copy-pasteable CLI invocations. The human types the decision in a Claude Code session, not at a shell. Drop the `agent-workbench complete <run-id> --accepted-by ...` form; keep one-line descriptions of what each decision *does*.
- **One source of truth for the banner content shape.** Same helper drives every agent-stopping transition's banner content (§2 already pins the *frame*; this task pins the *body* for `human_review` landings specifically). Wording stays in sync across `cmd_validate.py` and `cmd_followups.py`.
- **Conciseness is enforced.** ≤3 bullets in Summary of changes; ≤2 sentences in Summary of testing. Hard caps so it doesn't sprawl back into the bad-example shape. The renderer truncates rather than wraps.

### Banner shape for `human_review` landings

```
============================================================
STOP. State: human_review (human-owned).

Review:
  HUMAN_REVIEW.md: <absolute path to runs/<id>/HUMAN_REVIEW.md>

Summary of changes (≤3 bullets):
  - <bullet 1>
  - <bullet 2>
  - <bullet 3>

Summary of testing (≤2 sentences, or "None recorded."):
  <one to two sentences on what was run to confirm behavior — unit, dogfood, manual, etc.>

Diffstat:
  <N files changed, +X / −Y lines>

Next moves (human-triggered, type in a session):
  /complete <run-id>  — accept; auto-merges worktree branch into parent
  /bounce <run-id>    — send back to building with structured feedback
  /abandon <run-id>   — discard the run
============================================================
```

Where the body fields come from:

| Field | Source |
|---|---|
| HUMAN_REVIEW.md path | `metadata.run_dir(cfg, run_id) / "HUMAN_REVIEW.md"`, absolute. |
| Summary of changes | First ≤3 bullets from HUMAN_REVIEW.md's `## Summary of changes` section. Code-derived (already populated by `lib/human_review.py`'s renderer). If more bullets exist, truncate with a trailing `…(N more in HUMAN_REVIEW.md)`. |
| Summary of testing | One sentence built from `lib/metrics/lines.py` / QA report — names what was run (e.g. "unit tests"), pass/fail status (boolean — no counts), and whether a dogfood/manual run was recorded. If none recorded, the line is literally `None recorded.` |
| Diffstat | `git diff --shortstat <base_ref_sha>..HEAD` inside the worktree, formatted into the single line shown. (Depends on §3's `base_ref_sha` capture.) |
| Next moves | Static — one line per terminal action, with text descriptions, not full CLI commands. |

### Tasks

- [ ] **Extend `lib/cli/_stop_banner.py` (from §2) with a `human_review` body builder.** §2's helper currently maps landing state → static next-moves text. Add a sibling function `_build_human_review_body(cfg, run_id) -> str` that reads HUMAN_REVIEW.md, extracts the first ≤3 `## Summary of changes` bullets, builds the testing line from the QA report's outcome (`tests_passed: true` + `known_issues_count: 0` → "Unit tests passed; no known issues."; `false` → "Unit tests failed (see HUMAN_REVIEW.md)."; manual/dogfood mentions get a second sentence), and runs `git diff --shortstat` inside the worktree. `print_stop_banner(landing_state="human_review", run_id=...)` calls this builder; other landing states keep the current static text.
- [ ] **Truncation discipline.** The summary-of-changes extractor caps at 3 bullets. If HUMAN_REVIEW.md has more, append the literal line `  …(<N> more in HUMAN_REVIEW.md)`. Each bullet is single-line truncated at ~100 columns with `…` if longer. The testing line is capped at 2 sentences; if the renderer would produce a third, it's dropped.
- [ ] **Decision text replaces command text.** Rewrite the existing `Next moves` block — both in `cmd_followups.py`'s current output and in `cmd_validate.py`'s ad-hoc block — to the three-line form shown above (`/complete <run-id>`, `/bounce <run-id>`, `/abandon <run-id>`, each with a short description). Remove the `agent-workbench complete ... --accepted-by ...` shell form entirely.
- [ ] **Diffstat fallback.** If `base_ref_sha` is missing (pre-§3-fix runs), fall back to `git diff --shortstat <base_ref>..HEAD`. If that's empty (e.g. `HEAD..HEAD`), print `Diffstat: unavailable (base_ref unresolved — see §3).` rather than a misleading "0 files changed."
- [ ] **Verify HUMAN_REVIEW.md owns the canonical fields.** Sanity-check that branch name, commit SHA, full file-by-file diff, per-artifact links (brief / plan / build / QA / review / audit), and known-issues detail are all already in `lib/human_review.py`'s renderer output and the `templates/HUMAN_REVIEW.md` heading contract. They are today (verified 2026-05-24 against `runs/2026-05-24-fix-generated-lines-base-ref-head/HUMAN_REVIEW.md`); this task does not move them, only confirms the banner doesn't need to carry them.
- [ ] **Tests.**
  - Unit test for `_build_human_review_body`: fixture HUMAN_REVIEW.md files with (a) 2 bullets + tests passed + no manual testing, (b) 5 bullets + tests failed + manual dogfood recorded, (c) 0 bullets + no recorded testing. Assert truncation, testing-line shape, and the `None recorded.` fallback.
  - Snapshot test for the full `human_review` banner across two fixture runs (`happy/` and `bounce_pass2/` from the existing E2E set). Catches wording drift.
  - E2E extension: after `/followups` and after staged `/validate` lands in `human_review`, assert the stdout contains the absolute HUMAN_REVIEW.md path, exactly 3 `Next moves` decision lines, and either a diffstat line OR the "unavailable" fallback.

### Acceptance

- Running `/followups <id>` or `/validate <id>` (when either lands at `human_review`) prints a banner whose body has exactly the five sections in the order shown: `Review:`, `Summary of changes:`, `Summary of testing:`, `Diffstat:`, `Next moves:`.
- The `Review:` section prints the absolute path to HUMAN_REVIEW.md.
- The `Summary of changes:` section has ≤3 bullets, with a `…(N more)` line if HUMAN_REVIEW.md had more.
- The `Summary of testing:` section has ≤2 sentences, or the literal string `None recorded.` when no testing was recorded.
- The `Next moves:` section has exactly three lines: `/complete`, `/bounce`, `/abandon` — each with a one-line description, no `agent-workbench` shell form.
- Banner body is identical regardless of which CLI command produced the landing (driven by the single helper).
- HUMAN_REVIEW.md remains the canonical artifact for branch, commit SHA, full diff, test result counts, per-artifact links, known issues, and run timeline. The banner does not duplicate any of these.

### Non-goals

PR links (no support yet — out of scope until the workbench grows GitHub integration). Loud-card / color escape sequences (banner stays ASCII-only per §2). A banner shape for `done` / `abandoned` landings (those are terminals — §2's static text is enough). A banner shape for `ready` (planning landing — different decision set, different shape, separate task). Moving any field currently in HUMAN_REVIEW.md into the banner. Auto-opening the file in `$EDITOR` on landing (the human chooses when to read).

### Origin

Surfaced 2026-05-24 during a session reviewing the CLI's `human_review` landing output across the §2 dogfood run and the prior fix-generated-lines run. The two runs printed structurally different "what to review / what to decide" content for the same lifecycle event. The user pinned the rule: banner = pointer + minimum decision info; HUMAN_REVIEW.md = canonical detail.
