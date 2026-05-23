# TODO
## 2. Human Review polish

`HUMAN_REVIEW.md` is the human's landing page when a run moves into `human_review`, but today it's awkward to use:

- File pointers are relative (`stages/4_building/build.md`) — not clickable from a text editor.
- The `human_review` transition surfaces the run id but not the path to `HUMAN_REVIEW.md` itself, so the reviewer has to hunt for it.
- "Suggested first checks" reads like a manual QA script the reviewer is expected to run by hand; in reality validation already ran the tests — the reviewer wants the result, not the recipe.
- "Run timeline" is too generic — every run says "draft created", "brief transcribed", "plan written". It never names *what* the brief said, *what* the plan decided, *what* the build delivered, or *what* the reviewer accepted.
- No timestamps on the timeline, even though `events.jsonl` already carries ISO timestamps per event.
- No table-of-contents at the top, so click-to-open in a text editor is friction-heavy.

**Design principles**

- Treat `HUMAN_REVIEW.md` as a launchpad, not a checklist. Every interesting artifact should be one click away.
- Prefer absolute paths in the rendered file (most editors only auto-link absolute paths). Pair them with a relative-path table-of-contents at the top so the file is still readable when checked in.
- Trust validation. Surface *what was tested and what the result was*, not a script the human re-runs.
- The timeline must answer "what changed at each stage?" — pull specifics from `events.jsonl` (`payload.summary`, artifact paths, decision evidence) rather than templated prose.

**Tasks**

- [ ] **Surface the path on transition.** When a run moves into `human_review`, the slash command / CLI output (and the board card body) must print the absolute path to `HUMAN_REVIEW.md` so the reviewer can click it directly. Add a regression test that the `human_review` transition's stdout contains the absolute path.
- [ ] **Table of contents.** Render a TOC block at the top of `HUMAN_REVIEW.md` with one row per linked artifact. Each row carries a relative path (readable on GitHub / in git diffs) **and** the absolute path on the same line (clickable from VS Code / terminal). Suggested shape:
  ```markdown
  ## Files
  | Artifact | Relative | Absolute (click) |
  | --- | --- | --- |
  | Brief | `stages/2_shaping/brief.md` | `/Users/.../runs/<id>/stages/2_shaping/brief.md` |
  | Plan | `stages/3_planning/plan.md` | `/Users/.../runs/<id>/stages/3_planning/plan.md` |
  | Build (diffs + AC coverage) | `stages/4_building/build.md` | `/Users/.../runs/<id>/stages/4_building/build.md` |
  | QA report | `stages/5_validating/qa/report.md` | `/Users/.../runs/<id>/stages/5_validating/qa/report.md` |
  | Review decision | `stages/5_validating/review.md` | `/Users/.../runs/<id>/stages/5_validating/review.md` |
  | Follow-ups | `stages/6_followups/follow-ups.md` | `/Users/.../runs/<id>/stages/6_followups/follow-ups.md` |
  ```
  Only list files that actually exist (e.g. omit `follow-ups.md` when the run hasn't reached `6_followups`).
- [ ] **Change summary up top.** Replace "Where to start" with a `## Summary of changes` section: 3–5 bullets describing what the build delivered (files touched, ACs satisfied, test-count delta) followed by a single line `→ Full diff: <absolute path to build.md>`. The bullets are pulled from existing build.md fields (no new authoring step — this is a render-time projection of data the builder already wrote).
- [ ] **Replace "Suggested first checks" with "Manual testing performed".** This section reports what `validate` already ran:
  - Command (e.g. `python -m pytest tests/ -q`)
  - Outcome (`193 passed, 0 failed` — read from `qa/report.md` / `events.jsonl`)
  - One-line interpretation (`✓ all green` / `⚠ 2 known issues, see qa/report.md`)
  No imperative steps for the human to execute. If a check genuinely needs human eyes (UI screenshot review, etc.), surface it in a separate `## Needs human verification` block, but keep it empty by default.
- [ ] **Specific, timestamped run timeline.** Normalize each row to `[HH:MM:SS] STAGE — what specifically happened`. Pull `at` (existing ISO timestamp) and `payload.summary` / artifact paths from `events.jsonl`. Examples of the level of specificity wanted:
  - `[05:38:49] SHAPING — brief.md written: "audit unit tests for duplication across 6 modules; preserve regression locks"`
  - `[05:40:10] PLANNING — plan.md written: DR-001..DR-004 (combined-assertions folds; no prod changes; single-commit landing)`
  - `[05:52:18] BUILDING — baseline 193 tests; after pruning 134 tests (−59)`
  - `[06:11:02] VALIDATING — review.md decision: APPROVE; qa/report.md: 134 passed twice, 0 known issues`
  - `[06:11:47] HUMAN_REVIEW — handed off`
  Implementation note: extend the renderer to derive these rows from `events.jsonl` (`ArtifactWritten.payload.summary`, `TransitionApplied.from`/`to`, builder/validator events). Drop the freeform paragraph form entirely.
- [ ] **Tests.** Snapshot test the rendered `HUMAN_REVIEW.md` for the existing `happy/` and `bounce_pass2/` E2E fixtures. Add a unit test for the timeline projector that asserts each row has a timestamp, a stage name, and a non-templated description (reject rows that match a denylist like `"template staged"` or `"draft created"` with no further detail).

**Acceptance**

- `HUMAN_REVIEW.md` opens with a Files table whose absolute-path column is click-to-open in VS Code and the terminal.
- The `human_review` transition prints the absolute path to `HUMAN_REVIEW.md`.
- No section instructs the human to run shell commands; the manual-testing section reports outcomes only.
- Every timeline row is `[HH:MM:SS] STAGE — <specific description>`; none read like "brief transcribed" / "draft created" without further detail.
- E2E snapshot tests cover the rendered output for happy and bounce scenarios.

**Non-goals**

Redesigning the review *decision* flow (`stages/5_validating/review.md`); changing what the builder writes into `build.md`; adding new event types to `events.jsonl` (this work only consumes existing fields).

---

## 3. Token Efficiency tracking

Today we have no idea how expensive a run is. We don't know which stage burns the most tokens, whether bouncing through validation is a 2× or 10× tax, or which scope kinds (`implementation` vs `repair` vs `audit`) deliver the most accepted code per dollar. This work adds per-run token + cost + acceptance tracking — measurement only, no limits or budgets.

The eight metrics, as the user proposed:

1. `total_tokens_per_task` — sum of input + output + cache-read + cache-creation tokens across every Claude Code turn that fired inside the run's slash commands.
2. `tokens_per_passing_build` — `total_tokens_per_task / number of validate passes that returned APPROVE`. Higher = more retries to get green.
3. `first_pass_build_rate` — share of runs where the **first** `/validate` after the **first** `/build` returned APPROVE with no subsequent re-validation. Bounces (`request-changes`) and any post-validate session work that fed back into build / re-validate disqualify the run from "first pass." Computed at the **fleet** level (across runs), not per-run.
4. `attempts_per_success` — for runs that reached `done`, the count of `/build` → `/validate` cycles. For runs that reached `abandoned`, the same count up to the abandon transition.
5. `context_tokens_by_bucket` — input tokens broken out by where they came from. Initial buckets: `system_prompt`, `tool_defs`, `claude_md_and_agents_md`, `context_imports` (`@context/...` lazy-loads, once §1 lands), `slash_command_body`, `user_messages`, `assistant_history`, `tool_results`. Best-effort attribution from the transcript — fields that can't be cleanly separated go into `other` rather than being silently dropped.
6. `accepted_lines / generated_lines`:
   - `generated_lines` = **all** lines the agent wrote during the run across every draft, including discarded attempts. Sum of `+` lines across every `git diff` the builder produced, plus every artifact write captured in `events.jsonl` (`stages/*/*.md`, etc.), counted at write-time before any subsequent overwrite.
   - `accepted_lines` = `+` lines from `git diff --numstat <base_ref>...<merge_commit>` measured **after** the worktree merges back to its base branch and is torn down. Only lines that actually landed in the destination branch count.
   - A run that never merges has `accepted_lines = 0` regardless of how clean the build looked.
7. `repair_tokens_per_task` — tokens consumed by turns inside `/validate` re-runs, `/build` re-entries after a bounce, and any post-`validate` session work that re-touched build artifacts. Effectively: total tokens minus tokens consumed by the first happy-path pass through each stage.
8. **Total cost (generated)** and **Total cost (accepted)** — dollar cost of every token consumed during the run, computed against a per-model price table at the time the turn fired (Opus / Sonnet / Haiku input/output/cache-read/cache-creation rates). "Generated" = full cost of the run as it actually executed. "Accepted" = the same total, but only counted for runs whose terminal state is `done` (runs that ended in `abandoned` contribute `$0.00` to the accepted total at the fleet-level rollup). Replaces the original `cost_per_user_accepted_task` ratio — we want raw dollars in and dollars out, not a ratio.

**Design principles**

- Tracking only. No budgets, no thresholds, no warnings on the board. The data is for us to read, not for the system to enforce against.
- Data source is the Claude Code transcript at `~/.claude/projects/<project-slug>/*.jsonl`. Every turn already carries `message.usage.input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens` and a model id — we just need to correlate the transcript to a run.
- Per-run `metrics.jsonl` is the source of truth (one file per run, append-only, mirrors `events.jsonl`). A workbench-level rollup at `agent-workbench-live/metrics/index.json` is regenerated on demand from the per-run files — never edited by hand.
- Best-effort attribution. Where the transcript can't cleanly attribute a turn to a stage or a bucket, drop the value into an `other` bin rather than guessing. We'd rather under-report than mis-report.

**Storage layout**

```text
agent-workbench-live/
  metrics/
    index.json            # workbench-level rollup (regenerated on demand)
    prices.yaml           # per-model token prices, hand-edited
  runs/<run-id>/
    metrics.jsonl         # append-only, one row per turn / per measurement
    metrics-summary.json  # derived from metrics.jsonl, regenerated on read
```

`metrics.jsonl` row shape (draft — finalize during implementation):

```json
{"schema_version": 1, "kind": "turn", "at": "...", "stage": "building", "command": "/build",
 "model": "claude-opus-4-7", "usage": {"input": 12345, "output": 678, "cache_read": 90000, "cache_creation": 0},
 "bucket_attribution": {"system_prompt": 800, "tool_defs": 1200, "context_imports": 400, "...": "..."},
 "cost_usd": 0.0421, "transcript_ref": {"path": "...", "turn_id": "..."}}
{"schema_version": 1, "kind": "build_outcome", "at": "...", "attempt": 1, "validate_result": "request-changes"}
{"schema_version": 1, "kind": "line_count", "at": "...", "phase": "generated", "lines": 412}
{"schema_version": 1, "kind": "line_count", "at": "...", "phase": "accepted", "lines": 287, "merge_commit": "abc1234"}
```

**Tasks**

- [ ] **Transcript locator + correlator** — given a `run_id`, find the Claude Code transcript JSONL(s) that overlap the run's `created_at`..`updated_at` window for this project, and identify which turns belong to which slash command. Correlation strategy: match on the slash-command tool-use payload at turn start (`/shape`, `/plan`, `/build`, `/validate`, `/followups`) plus the run's working directory. Output a list of `(turn, stage, command)` tuples. Pure function over transcript bytes — no I/O in the unit tests; feed it fixture transcripts. Write at `lib/metrics/transcript.py`.
- [ ] **Bucket attribution** — for each turn in the correlated list, attribute input tokens to one of the buckets enumerated above. Pull bucket boundaries from the transcript message structure (system prompt, tool defs in `tools`, user/assistant role markers, `@context/...` import expansions, tool-result blocks). Unattributable bytes fall into `other`. Write at `lib/metrics/buckets.py` with a fixture-driven test that covers every named bucket plus `other`.
- [ ] **Price table** — author `agent-workbench-live/metrics/prices.yaml` with current Anthropic per-model rates (Opus 4.6 / 4.7, Sonnet 4.5 / 4.6, Haiku 4.5) split into `input_per_mtok`, `output_per_mtok`, `cache_read_per_mtok`, `cache_creation_per_mtok`. Loader at `lib/metrics/prices.py` validates the file shape and returns a `dict[model_id, Rates]`. Cost computation = sum of `(tokens * rate) / 1_000_000` per kind. Unknown model = warn and skip (no synthetic price).
- [ ] **`metrics.jsonl` writer** — `lib/metrics/writer.py` with a single public `record_run_metrics(run_id) -> None` entry point. Walks the transcript via the correlator, attributes via the bucketer, prices via the table, and emits `metrics.jsonl` rows for every turn plus `build_outcome` rows (one per `/validate` result, read from `events.jsonl`). Idempotent: re-running on the same run replaces the file rather than appending duplicates.
- [ ] **Line-count capture** — `lib/metrics/lines.py`. `generated_lines` is computed at run-completion time by walking `events.jsonl` for `ArtifactWritten` rows + git history of the worktree (`git log --numstat <branch>`). `accepted_lines` is computed at the merge boundary: when a run transitions to `done` and the worktree is torn down, capture `git diff --numstat <base_ref>...<merge_commit>` and write a `line_count` row. If the worktree is torn down without a merge commit (rare; record the case), `accepted_lines = 0`.
- [ ] **Wire into the lifecycle** — call `record_run_metrics(run_id)` (a) after every `/validate` transition (so partial metrics exist for in-flight runs) and (b) at the terminal `done` / `abandoned` transition (so the file is final). Hook in via the existing transition machinery; do **not** ask slash commands to self-report.
- [ ] **Per-run summary** — `lib/metrics/summary.py` reads `metrics.jsonl` and returns a `RunMetricsSummary` dataclass with all eight metric values. Cached on `(run_id, mtime(metrics.jsonl))`. Used by every downstream renderer.
- [ ] **Workbench rollup** — `lib/metrics/rollup.py` walks every `runs/*/metrics.jsonl`, derives the cross-run metrics (`first_pass_build_rate` per scope kind, totals across scope kinds, dollars by month), and writes `agent-workbench-live/metrics/index.json`. Pure regeneration — never edits per-run files.
- [ ] **CLI: `agent-workbench metrics`** — three forms:
  - `agent-workbench metrics <run-id>` — prints the eight metrics for one run, plus a per-stage breakdown and the bucket histogram. Plain text by default; `--json` for machines.
  - `agent-workbench metrics --all` — prints the workbench rollup (leaderboard ordered by `tokens_per_passing_build`, totals, first-pass rate per scope kind).
  - `agent-workbench metrics --rebuild` — forces a rollup regeneration.
- [ ] **HUMAN_REVIEW integration** — append a `## Token efficiency` block to the rendered `HUMAN_REVIEW.md` (coordinate with §2). One line per metric, plus a one-line cost summary (`generated: $X.XX · accepted: $Y.YY pending merge`). Only render the block when `metrics.jsonl` exists.
- [ ] **Live board card band** — new band below the existing meta line, rendered as `tokens 12.3k · build 1/2 · $0.42`. **No loud-card behavior** based on budget thresholds — the user explicitly does not want budget enforcement. The band renders for every state once metrics exist; it's read-only telemetry.
- [ ] **Tests** —
  - Unit tests for `transcript.py` (fixture transcripts → expected turn list), `buckets.py` (every bucket + `other`), `prices.py` (valid file, malformed file, unknown model), `lines.py` (generated-only run, merged run, abandoned run).
  - Integration test: drive the existing E2E `happy/` and `bounce_pass2/` fixtures through `record_run_metrics`, snapshot the resulting `metrics.jsonl`, assert summary values match hand-computed expectations.
  - CLI smoke test for all three `agent-workbench metrics` forms.

**Acceptance**

- After any run reaches `human_review` or beyond, `runs/<id>/metrics.jsonl` exists and contains at least one `turn` row per Claude Code turn fired inside the run's slash commands.
- `agent-workbench metrics <run-id>` prints all eight metrics for a finished run, with `accepted_lines` non-zero only after the worktree has merged.
- `agent-workbench metrics --all` reports a fleet-level `first_pass_build_rate` (a percentage, not a per-run boolean).
- `HUMAN_REVIEW.md` carries a `## Token efficiency` block for runs that have a `metrics.jsonl`.
- The live board card shows the `tokens · build · $` band with no threshold-driven loudness.
- E2E fixture runs (`happy/`, `bounce_pass2/`) produce snapshot-tested `metrics.jsonl` outputs.

**Non-goals**

Budgets, limits, or warnings; per-turn live metering (we batch at transition time from the transcript); supporting non-Claude-Code LLMs; price discovery — `prices.yaml` is hand-maintained; cross-project rollups — scope is this workbench only; cost-allocation per developer / team — run-level only.

---

## 4. Token efficiency — pass 2: stop bleeding `cache_read`

### Why this is here

§3 shipped per-run metrics, but on its own dogfood run (`runs/2026-05-22-token-efficiency-tracking/metrics.jsonl`) the numbers are:

| Bucket | Tokens | Share | Bucketed by §3? |
|---|---:|---:|:---:|
| fresh input | 2,934 | 0.0024% | yes |
| output | 425,478 | 0.34% | n/a |
| cache_creation | 1,178,364 | 0.95% | **no** |
| cache_read | **121,786,040** | **98.7%** | **no** |
| **total** | **123,392,816** | | |
| **cost** | **$236.73** | | |

§3 only buckets `input_tokens`. That accounts for **0.003% of cost**. The renderer literally prints "cache_read not bucketed" (`lib/cli/cmd_metrics.py:88`). So measurement is half-built. Worse: 100% of 621 turns on that run landed in `stage=other, command=""` — the slash-command correlator silently broke, so there isn't even a per-phase split. Both are §3 gaps that §4 closes.

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
- **Attribution before reduction.** §3's bucketer is the only way to know whether mitigations actually worked. Land the cache buckets first; measure the impact of each subsequent task.
- **Honest under-attribution beats confident mis-attribution.** Cache buckets use the same heuristic-and-residual-into-`other` pattern as input buckets.

### Tasks — Part A: visibility (you can't fix what you can't see)

- [ ] **A1. Fix the slash-command correlator.** `lib/metrics/transcript.py:correlate()` + `_cwd_matches()` are landing 100% of turns into `stage=other, command=""` on the §3 dogfood run. Diagnose first (suspect: worktree-path resolution vs. `meta.target.worktree.path`, OR `current_command` not propagating across record types). Land a regression test that points at the production transcript's `session_id` and asserts non-empty `stage` distribution. Without this, every per-phase metric is broken.
- [ ] **A2. Bucket `cache_read_input_tokens` and `cache_creation_input_tokens`.** Extend `lib/metrics/buckets.py:attribute()` to return three dicts: existing `input_buckets` plus new `cache_read_buckets` and `cache_creation_buckets`. Computation: walk the transcript prefix per turn (accumulate user/assistant/tool-result text monotonically), apply the existing 4-chars/token heuristic per region, scale to the API's `cache_read_input_tokens` / `cache_creation_input_tokens` counts respectively, residual into `other`. Add the missing buckets: `system_prompt` (constant estimate or first-turn measurement), `tool_defs` (count of tools × ~150 tokens/tool), `repo_files` (tool_results matching the `Read` output gutter pattern `^\s*\d+\t`), `validation_context` (tool_results within a `/validate` span), `generated_drafts` (assistant turns whose body contains markdown headers — proxy for review.md / build.md drafts). Keep `claude_md_and_agents_md`, `context_imports`, `slash_command_body`, `user_messages`, `assistant_history`, `tool_results`, `other`.
- [ ] **A3. Carry session prefix through `correlate()`.** Extend `CorrelatedTurn` with three new tuple fields: `prefix_user_messages`, `prefix_assistant_messages`, `prefix_tool_results`. Unlike the existing `pending_*` per-turn buffers, these accumulate monotonically across the session so A2's bucketer can attribute the cache prefix. Don't clear them on turn boundary.
- [ ] **A4. Surface the new buckets.** Update `RunMetricsSummary` (`lib/metrics/summary.py`) with `cache_read_by_bucket: dict[str, int]` and `cache_creation_by_bucket: dict[str, int]`. Update `_render_summary_plain` (`lib/cli/cmd_metrics.py:88-90`) to drop the "input tokens only" disclaimer and render three sub-sections: `input buckets`, `cache_read buckets`, `cache_creation buckets`.
- [ ] **A5. Per-turn `metrics.jsonl` row update.** `lib/metrics/writer.py:177-199` writes one `bucket_attribution` key today; add `cache_read_attribution` and `cache_creation_attribution` next to it. Bump `schema_version` to 2; summary reader tolerates both.
- [ ] **A6. Cache-miss visibility.** Add `cache_misses: int` to `RunMetricsSummary`, computed as the count of turns where `cache_creation > 1000`. Surface as `cache misses: N` in the per-run summary. Helps detect long pauses that re-wrote the cache (5-minute TTL).
- [ ] **A7. Re-baseline `tokens_per_passing_build`.** Today it's `total_tokens / approves` where `total_tokens` is dominated by `cache_read`, so the metric tracks session length more than agent efficiency. Add `billable_net_per_passing_build = (input + output + cache_creation) / approves` — excluding `cache_read` — alongside. Keep the original for continuity; render both.
- [ ] **A8. Session-turn-count metric.** Add `largest_session_turns: int` and `largest_session_id: str` to `RunMetricsSummary`. Surface in the per-run summary. Required input for A9 and Part B.
- [ ] **A9. Board: session-staleness band.** `lib/board/snapshot.py` already renders a metrics band per §3. Append a `turns: N` indicator when `largest_session_turns > 100`. Read-only nudge; no loud-card behavior.

### Tasks — Part B: mitigation (largest impact first)

- [ ] **B1. Promote fresh sessions to a lifecycle discipline in `agent-workbench-live/AGENTS.md`.** Add a `## Session discipline` section. Rules:
  - **Always start a new Claude Code session at the `/validate` boundary** when the building session has > 100 turns. The handoff is the run_id + worktree path; nothing else needs to carry over.
  - **Always start a new session between independent runs.** A new `/new-run` for an unrelated task = exit and relaunch first.
  - **Stay in the same session for `/shape` → `/plan` → `/build`.** These share useful context and the cache amortizes well.
  - **Restart when you see Claude Code's auto-compact notice.** That's a signal you're already paying for a lot of prefix; better to restart than let it compact mid-task.
  - Include the rationale (one paragraph on the prefix-grows-monotonically mechanic; reference the §3/§4 measurement). Discipline only sticks if the "why" is in front of the reader.
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
- [ ] **B6. Audit and shrink CLAUDE.md / AGENTS.md weight.** On a 621-turn session, each 1k tokens of always-loaded instructions costs ~621k tokens of `cache_read`. Read `~/.claude/CLAUDE.md`, repo-root `AGENTS.md`, `agent-workbench-live/AGENTS.md`. For each: identify content that's (a) duplicated across files, (b) only relevant to a specific stage (move into the slash-command body instead — loaded once per invocation), (c) historical/contextual reference that doesn't drive agent behavior (move to docs/architecture.md or LOG.md). Target: cut combined always-loaded instruction weight by 30%+. Land as a single PR with before/after token counts measured via §3's metrics on a same-length dogfood run.
- [ ] **B7. Subagent-first read strategy for `/build` and `/validate`.** Today, file reads happen in the master session and their results stick in the master prefix forever. Update `agent-workbench-live/AGENTS.md` § "Subagent discipline" to require: when a stage needs to read more than 3 files for exploration (not edits), route through an `Explore` subagent. The subagent returns a summary; the master keeps a tiny prefix. Add concrete examples to `.claude/commands/build.md` and `.claude/commands/validate.md`. This is the single most impactful change after fresh sessions — it bounds how big the build session's own prefix can grow.
- [ ] **B8. Tool-output budget guidance.** Add to `agent-workbench-live/AGENTS.md`: a soft budget per Bash tool call (Read outputs > 2k tokens → use `head`/`tail`/grep; `git log` → cap with `-n 20`; `git diff` → `--stat` first, full diff only if needed). Document the pattern so it sticks across sessions. Not enforced — guidance only.

### Tasks — Part C: tests + acceptance gating

- [ ] **C1. Fixture-driven cache-bucket attribution test.** Synthetic transcript with a 100k-token prefix that includes all bucket types in known proportions. Assert `cache_read_by_bucket` attributes correctly within ±2% (the scale step adds rounding noise).
- [ ] **C2. Regression test for the correlator fix.** Load the §3 dogfood run's actual transcript via `find_transcripts`. Assert that after the A1 fix, > 50% of turns have non-`other` `stage`.
- [ ] **C3. Snapshot test for `validate-context.md`.** Drive the existing `happy/` and `bounce_pass2/` E2E fixtures through `validate --init`; snapshot the generated file. Catches regressions in the deterministic builder.
- [ ] **C4. CLI smoke test.** `agent-workbench metrics <id>` output includes the three bucket sub-sections, `cache misses: N`, `billable_net_per_passing_build`, and `turns: N`.
- [ ] **C5. End-to-end cost measurement.** After all Part B tasks land, run a `happy/` E2E fixture and measure the new `cache_read` total. Acceptance: total `cache_read` for the run is ≥ 40% lower than the §3 dogfood baseline (123.4M → ≤ 74M for an equivalent workload).

### Acceptance

- `agent-workbench metrics <run-id>` prints `cache_read buckets` and `cache_creation buckets` that sum (within ±2%) to the run's `total_cache_read` / `total_cache_creation`.
- On the §3 dogfood run, re-running `agent-workbench metrics <id> --record` produces a per-turn `stage` distribution that is no longer 100% `other`.
- `/validate <id>` on a fresh run produces `stages/5_validating/validate-context.md` and `blast-radius.txt` before any LLM call.
- `.claude/commands/validate.md` instructs reading `validate-context.md` instead of brief/plan/build separately.
- `agent-workbench-live/AGENTS.md` has a `## Session discipline` section that names the fresh-session-at-validate rule, the new-session-between-runs rule, and the why.
- `validate --init` prints the full fresh-session handoff block (not just a one-line hint) when `largest_session_turns > 100`.
- `~/.claude/CLAUDE.md` + repo `AGENTS.md` files have measurably-shrunk always-loaded weight (before/after counts in the LOG.md entry).
- `agent-workbench-live/AGENTS.md` § "Subagent discipline" prescribes Explore subagents for multi-file reads in `/build` and `/validate`.
- E2E fixture cache_read drops by ≥ 40% vs. the §3 baseline.

### Non-goals

Enforcing cache_read budgets (no hard limits, no warnings that block transitions); auto-restarting Claude Code (no harness automation that exits the user's session); rewriting `lib/metrics/transcript.py` correlator from scratch (it's load-bearing for §3 — patch, don't rewrite); cross-session de-duplication of cached prefix (Anthropic's cache layer is what it is — we work around it via session discipline, not at the API layer); supporting non-Claude-Code LLMs.

### How far this gets us — and what it doesn't solve

After §4 lands, the answer to "where did the cache_read go" is no longer "unknown." The validate phase's contribution drops materially (curated context + fresh session + pre-computed blast radius). The fixed per-turn overhead drops (CLAUDE.md/AGENTS.md audit). Multi-file exploration stops accumulating in the master prefix (subagent routing).

What §4 still doesn't solve and would need future runs:

- **Build-phase compaction.** A `/build` that lasts 200+ turns inside one session still grows its own prefix. §4 mitigates via fresh sessions at the validate boundary, but doesn't address build-mid checkpointing. A future `agent-workbench build --checkpoint` could prompt the model to write `build-progress.md` and recommend a session refresh mid-build.
- **Per-turn cost throttling.** §4 reports per-turn cost but doesn't throttle. Throttling would require either model-side self-summarization or harness-level hard limits — both more invasive than §4's scope.
- **Anthropic-side: auto-compact timing.** Claude Code's auto-compaction isn't aligned to the lifecycle (build → validate boundary). Only Anthropic can change that.

---

## 5. Fix generated_lines for base_ref="HEAD" runs

`lib/metrics/lines.py:count_generated()` runs `git log --numstat <base_ref>..HEAD` to sum `+` lines across the worktree's commit history. The workbench config defaults `base_ref: HEAD` (`agent-workbench.yaml:14`), and `metadata.target.repo.base_ref` is stored as that literal string. The dotted range `HEAD..HEAD` resolves to "no commits" — so `generated_lines` reports 0 for every run that uses the default, regardless of how many commits the builder landed.

Observed on the §3 dogfood run: 3 commits with ~2.4k inserted lines across them; `generated_lines: 0`. Same gap will hit every future run that doesn't override `base_ref`.

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
- The §3 dogfood run (`2026-05-22-token-efficiency-tracking`) reports non-zero `generated_lines` after the lazy resolver lands — either via re-running `metrics --record` on the existing run, or via a one-shot backfill.
- `tests/test_metrics_lines.py` has a regression test that pins the symbolic-ref behavior.

**Non-goals**

Changing the default `base_ref`; making the metrics writer infer the base from `git merge-base`; supporting non-git worktrees.

**Origin**

Discovered during the §3 dogfood run (`runs/2026-05-22-token-efficiency-tracking/stages/6_followups/follow-ups.md` § "Fix generated_lines for base_ref=\"HEAD\" runs"). Promoted from per-run follow-up to workbench-level TODO so it's actioned outside the original run.
