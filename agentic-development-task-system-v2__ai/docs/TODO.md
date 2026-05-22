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
