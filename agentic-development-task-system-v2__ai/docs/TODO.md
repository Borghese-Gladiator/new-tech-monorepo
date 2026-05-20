# TODO

Next round of work after V1. Each section captures one idea — what it is, why we want it, and the concrete pieces to build.

Order reflects priority: **Renovate task workflow** is first because it reshapes the on-disk layout every other track touches — doing it last would mean rework. Worktree naming is next as a small, isolated warm-up. Then board, summary, E2E, context graph.

---

## 1. Renovate task workflow

Streamline the run lifecycle so a human reviewer can land in a finished run and immediately see (a) what changed, (b) what was validated, and (c) what to do next — without sifting through 15 files. Make the build loop, follow-up generation, and per-stage archiving first-class instead of implicit.

**Motivation.** A typical finished run today produces ~15 artifacts in a flat directory (`raw-idea.md`, `brief.md`, `brief-v2.md`, `preflight.md`, `plan.md`, `assumptions.md`, `decisions.md`, `implementation-summary.md`, `diff-summary.md`, `review.md`, `qa/`, `audit.md`, `handoff.md`, `metadata.yaml`, `events.jsonl`). Real reviewer feedback: *"I'm a human reviewer and not sure where to even start."* The current layout faithfully encodes the stage model but forces the reviewer to reverse-engineer which 2–3 files matter for them right now. Also, two behaviors are invisible to the lifecycle today: the builder's test/fix loop runs implicitly with no recorded iteration count, and follow-up work surfaced after validation has nowhere to live.

### 1a. Directory layout: `stages/` vs `archive/`

Split the run directory so semantics are obvious from the filesystem. `stages/` holds **canonical, current** outputs (the source of truth downstream agents and reviewers read). `archive/` holds **superseded** versions (bounce variants, discarded build iterations, replaced plans) — forensic only, never required reading.

Target layout for a finished run:

```
runs/<run_id>/
  stages/
    draft/raw-idea.md
    shaping/brief.md
    planning/plan.md            ← includes "Decisions & assumptions" section
    building/build.md           ← merge of implementation-summary.md + diff-summary.md
    validating/review.md
    validating/qa/
    followups/follow-ups.md
  archive/
    shaping/brief-v1.md         ← if bounced; current brief.md remains in stages/
    planning/plan-v1.md         ← if planning re-ran
    building/build-iter-1.md    ← discarded build iterations
  HUMAN_REVIEW.md               ← replaces handoff.md; persona-keyed hub + "Run timeline" section (folds audit.md)
  metadata.yaml
  events.jsonl
```

Top-level entries when a reviewer lands: **5** (`stages/`, `archive/`, `HUMAN_REVIEW.md`, `metadata.yaml`, `events.jsonl`). Down from 15.

- [ ] Update `lib/lifecycle.py` (or equivalent) so successful stage exit moves that stage's outputs into `stages/<stage>/`. Per-stage archiving on success, not one big sweep at the end.
- [ ] Define supersession rules — when something moves to `archive/<stage>/`:
  - Bounce from `human_review → building` archives current `stages/building/` and `stages/validating/` as `build-v1.md`, `review-v1.md`, etc. before the new build starts.
  - `/bounce` on a brief moves the prior `stages/shaping/brief.md` to `archive/shaping/brief-v1.md` before writing the new one. (Replaces the current `brief-v2.md` naming, which conflates "current" and "old.")
  - Discarded build iterations land at `archive/building/build-iter-<N>.md`.
- [ ] Versioning convention: `<name>-v<N>.md` where N is supersession order (v1 = oldest superseded). The *current* version always lives in `stages/`, never with a `-vN` suffix.
- [ ] `archive/` is never linked from `HUMAN_REVIEW.md`. Forensics only.
- [ ] Migration: existing in-flight runs created before this change keep their flat layout. New runs get the new layout. Add a one-line note in `lifecycle.md`.
- [ ] **Empty-directory pruning on completion.** A completed run with no bounces, no QA recordings, and no traces shouldn't leave `archive/`, `qa/recordings/`, or `qa/traces/` as empty stubs. On transition into `human_review`, prune any empty subtree under `stages/`/`archive/`/`qa/`. The "5 top-level entries" promise in 1a's test matrix only holds if empty `archive/` is omitted.

### 1b. File mergers — cut the count, not the audit fidelity

Several files always travel together with the same author, same stage, and same audience. Merge them as sections.

- [ ] `assumptions.md` + `decisions.md` → folded into `plan.md` as a final **"Decisions & assumptions"** section. Same author (planner), same audience (builder). Assumptions are the unverified subset of decisions; no reason to split.
- [ ] `implementation-summary.md` + `diff-summary.md` → merged into a single `build.md`. Sections: `What changed`, `Files changed`, **`Reviewer reading order`** (new — 3–7 files in recommended order, each with a one-line "what to look for here"; without it, `Files changed` is just an inventory), `Acceptance criteria coverage` (required; every brief AC mapped to a test path or an explicit "not tested — because …" justification — transition out of `building` rejects if a row is missing either), `Deviations from plan`, `Known issues`, `Commands run`, **`Documentation touched`** (new — see 1d).
- [ ] `preflight.md` → folded into `plan.md` as a `Preflight` section.
- [ ] `audit.md` → folded into `HUMAN_REVIEW.md` as a bottom **"Run timeline"** section. The timeline is reviewer context, not a separate file; it belongs next to the routing.
- [ ] `handoff.md` → renamed/replaced by `HUMAN_REVIEW.md` (see 1c). Not just a rename — the content model changes from "summarize every artifact" to "route by reviewer persona."
- [ ] **Not merged**: `follow-ups.md` stays separate (actionable state, structured frontmatter for CLI spawning), `review.md` stays separate (too large + different audience), `qa/` stays separate (it's a directory).

### 1c. `HUMAN_REVIEW.md` — the entry point

Replace `handoff.md` with a persona-keyed hub. ~20 lines of routing, plus the folded-in timeline section, plus the smoke checklist.

- [ ] Hub section: short list keyed by what the reviewer wants to do. Each line links into `stages/...`:
  - "Want to see diffs? → `stages/building/build.md`"
  - "Want to verify QA? → `stages/validating/qa/report.md` + `stages/validating/qa/commands.txt`"
  - "Want to confirm each AC is tested? → `stages/building/build.md` § Acceptance criteria coverage"
  - "Want to argue with decisions? → `stages/planning/plan.md` § Decisions & assumptions, then `stages/validating/review.md`"
  - "Want to see what's next? → `stages/followups/follow-ups.md`"
- [ ] **"Suggested first checks" section** — MANDATORY in every reviewer-facing handoff artifact. An ordered, numbered, copy-pasteable checklist that walks the reviewer from a clean checkout to a verified working feature in ~10 minutes. Format requirements:
  - **Automatable steps first, as a single fenced bash block** the reviewer can copy-paste in one go (install, build, automated tests, server/app start). Don't interleave commands with prose — the poker run's handoff did, and the reviewer has to read every line to extract what's executable.
  - **Then numbered manual / browser steps**, each with a one-line description plus exact UI actions and concrete test data (e.g. "nickname `Tim`"). At least one targeted inspection (devtools / logs / DB query), and any AC that lives outside automated QA.
  - Closes with an explicit "if steps 1–N pass, the run is delivered" line, and calls out which steps the human must do that QA couldn't.
  - Reference exemplar to mirror: the "Suggested first checks" section from the python-poker-first run's `handoff.md` (install → pytest → start server → two-browser E2E → websocket frame inspection → tunnel test) — but reorganized per the bullet above (commands consolidated, manual steps separated).
- [ ] (Stretch) Emit `stages/validating/qa/smoke.sh` alongside `commands.txt` containing the automatable block verbatim. Reviewer runs `bash stages/validating/qa/smoke.sh`; non-zero exit = something the builder claimed works doesn't.
- [ ] **"Run timeline" section** (folded `audit.md`) — chronological summary rendered from `events.jsonl` + artifacts.
- [ ] `validating` (or the new `followups` stage) must reject a `HUMAN_REVIEW.md` that lacks the "Suggested first checks" section.

### 1d. Documentation as a deliverable

Repo-doc updates (README, AGENTS.md, CHANGELOG, inline comments in the *target* repo) are currently invisible to the lifecycle. Make them an explicit field of `build.md`.

- [ ] Add a required **"Documentation touched"** section to `build.md`. Lists repo-doc changes made in the target repo, or an explicit justified "none needed — because …". Silent skipping is not a valid answer.
- [ ] `validating` adversarially verifies the doc claim against the diff. If the section says "updated README" but the README is unchanged in the diff, the review must flag it.

### 1e. Build loop as a first-class concept

Surface the test/fix iteration that currently runs invisibly inside `building`.

- [ ] Add `build_iterations: <int>` to `metadata.yaml`, incremented each time the builder runs tests + fixes.
- [ ] Add `build_exit_reason` to `metadata.yaml`, one of: `tests_green | max_iterations_hit | hard_block | manual_stop`.
- [ ] Add `max_build_iterations` to run config (default 5). Hitting the ceiling exits `building` with reason `max_iterations_hit` rather than silently giving up — the human sees this in `HUMAN_REVIEW.md`.
- [ ] Transition out of `building` rejects metadata missing `build_iterations` or `build_exit_reason`.
- [ ] `HUMAN_REVIEW.md`'s "Run timeline" includes a one-line build-loop summary: "Build ran N iterations, exited with reason X."

### 1f. New stage: `followups`

Follow-up brainstorming runs **after** `validating` completes, as its own stage between `validating` and `human_review`. Keep validation backward-looking (adversarial review against the brief); keep follow-ups forward-looking (what should the next run tackle). Mixing them biases the review.

- [ ] Add `followups` to the lifecycle in `docs/lifecycle.md`. New canonical flow:
  ```
  draft → shaping → planning → ready → building → validating → followups → human_review → done
  ```
- [ ] Stage contract for `followups`:
  - **Owner**: post-validation agent (separate from reviewer agent).
  - **Reads**: `stages/building/build.md`, `stages/validating/review.md`, `stages/validating/qa/`, `stages/planning/plan.md`, **`events.jsonl` filtered to `BounceRequested`**, **any prior `archive/shaping/brief-v<N>.md` and `archive/planning/plan-v<N>.md`** (so scope deferred during a bounce is visible to the follow-ups author).
  - **Produces**: `stages/followups/follow-ups.md` — 1–5 mini-briefs, or explicit "no follow-ups identified" (an empty file is not valid). Output must distinguish items raised in this run's review/QA from items explicitly deferred during bounces — deferrals must not be silently lost between briefs.
  - **Exit evidence**: `followups_path` set in metadata and non-empty.
- [ ] `follow-ups.md` format — each mini-brief has YAML frontmatter so the CLI can read them later:
  ```yaml
  ---
  title: <short title>
  motivation: <why this matters>
  suggested_scope: <one-run-sized chunk>
  category: tech_debt | scope_extension | bug_risk | refactor | docs | deferred_from_bounce
  ---
  ```
  The `deferred_from_bounce` category is reserved for items that appeared in a prior brief/plan, were dropped via `/bounce`, and were not picked up in the current run's scope.
- [ ] Transition into `human_review` rejects when `follow-ups.md` is missing or empty (the "none identified" answer must be explicit).
- [ ] `HUMAN_REVIEW.md` hub links to `stages/followups/follow-ups.md` ("Want to see what's next?").
- [ ] (Stretch, later) `agent-workbench followup spawn <run_id> <n>` — create a new `draft` run pre-populated from follow-up #n of the named run.

### 1g. Blast radius in review

Add a bounded impact analysis to catch scope creep and surprise coupling.

- [ ] Add a **"Blast radius"** section to `review.md`. Format: files touched in the diff, then callers of touched symbols, then callers-of-callers. Stop at depth 3.
- [ ] Flag in `review.md` when blast radius is wider than the brief suggested — early signal of scope creep.
- [ ] Depth is fixed at 3 for V1. Configurability is a stretch.

### Tests

- [ ] Unit: transition out of `building` rejects metadata missing `build_iterations` / `build_exit_reason`.
- [ ] Unit: transition out of `validating` succeeds only if the `followups` stage can start (i.e., required reads exist).
- [ ] Unit: transition into `human_review` rejects when `follow-ups.md` is missing or empty.
- [ ] Unit: transition into `human_review` rejects when `HUMAN_REVIEW.md` lacks a "Suggested first checks" section.
- [ ] Unit: `follow-ups.md` frontmatter parser accepts the 5 categories and rejects others.
- [ ] Unit: archiving moves files to `stages/<stage>/` on success and to `archive/<stage>/<name>-v<N>.md` on supersession; never both.
- [ ] Unit: back-compat read path — runs created before this change (flat layout) still load.
- [ ] Manual: run a fresh task end-to-end and confirm:
  - Top-level directory contains exactly `stages/`, `archive/`, `HUMAN_REVIEW.md`, `metadata.yaml`, `events.jsonl`.
  - `stages/planning/plan.md` contains a "Decisions & assumptions" section and a "Preflight" section.
  - `stages/building/build.md` exists (no separate `implementation-summary.md` / `diff-summary.md`) and contains a "Documentation touched" section.
  - `metadata.yaml` includes `build_iterations` and `build_exit_reason`.
  - `stages/followups/follow-ups.md` exists with structured frontmatter.
  - `stages/validating/review.md` contains a "Blast radius" section with concrete depth-3 traversal.
  - `HUMAN_REVIEW.md` is ~20 lines of routing + a "Suggested first checks" checklist + a "Run timeline" section.
  - Land in the run directory cold as a reviewer: know where to start within 30 seconds of opening `HUMAN_REVIEW.md`.
- [ ] Manual: run a bounce cycle and confirm the prior `stages/building/` and `stages/validating/` land under `archive/` with `-v1` suffixes, and the new build outputs replace them in `stages/`.

---

## 2. Better worktree name

Today `worktree_name` defaults to the slug of the brief title — fine for short titles but loses information for longer ones, and there's no signal of *what stage* the work is in or *which repo* it targets when you're staring at a `worktrees/` directory.

- [ ] Audit current naming: `worktrees/<repo_name>/<slug>`. Document the failure modes (collisions when two runs share a slug; opaque names when slugs are truncated; no date hint).
- [ ] Decide on a new template. Candidate: `<YYYYMMDD>__<slug>` (matches the existing `LOCAL_worktrees` convention this repo uses — see `202605_agent_workbench_v2`). Alternative: `<run_id>` directly (already date-prefixed + slug, guaranteed unique).
- [ ] Update `agent-workbench.yaml.defaults.worktree_name_template` and the resolver in `lib/run_ids.py`.
- [ ] Decide whether `branch_name` follows the same pattern. Current: `agent/<worktree_name>`. Probably stays — but verify the new template doesn't break git's branch name rules.
- [ ] Migration story for existing in-flight runs: don't rename them. New template applies only to runs created after the change. Add a one-line note in `lifecycle.md`.
- [ ] Update integration tests that assert on worktree paths.
- [ ] Update `AGENTS.md` and `README.md` examples.
- [ ] (Stretch) Allow the user to override per-run via `new-run --worktree-name <name>` — already supported; just make sure the slug-sanitizer doesn't strip the new template's separators (`_`, double-underscore).

## 3. Task board

Right now run state is scattered across `runs/<run_id>/metadata.yaml` files. To see what's in flight you have to `agent-workbench list` and squint. A task board surfaces all runs grouped by lifecycle state so humans can see queue depth and what needs attention.

- [ ] Decide format. Default: terminal-rendered Kanban (`agent-workbench board`) with one column per state (`draft`, `shaping`, `planning`, `ready`, `building`, `validating`, `human_review`, `done`, `abandoned`). Stretch: an HTML render written to `runs/_board.html` for browser viewing.
- [ ] Add `agent-workbench board` subcommand. Reads every `runs/*/metadata.yaml`, groups by status, prints columns with `run_id`, age (since `updated_at`), `repo_name`, branch.
- [ ] Highlight runs that have been in `human_review` for more than N hours (configurable in `agent-workbench.yaml.board.stale_human_review_hours`).
- [ ] Hide terminal states by default; `--all` includes `done` and `abandoned`.
- [ ] Slash command `/board` — thin wrapper.
- [ ] (Stretch) `agent-workbench board --html <path>` writes a single self-contained HTML file. No server, no JS framework — just a static dump regenerated on demand.
- [ ] (Stretch) Per-run "blocker" field in metadata so the board can show *why* a run is stalled in `human_review` (e.g., "waiting on QA env").

## 4. Activity log summary

Per-run, human-readable rollup of what a single run produced — not a cross-run digest. Goal: open one file and see at a glance *what changed* and *what was added* in that run, including any mid-flight course corrections from `/bounce`. `events.jsonl` is the source of truth but it's noisy (every `CommandRun` and `ArtifactWritten`); `audit.md` is a chronological dump. Neither answers "what did this run actually do?" in one screen.

- [ ] Add `agent-workbench summary <run_id>` subcommand. Default target: the run identified by `<run_id>`; with no arg, the most recently updated run. Writes (or refreshes) `runs/<run_id>/summary.md`.
- [ ] **Keep it current.** The summary must be regenerated on every state transition and every artifact write so it never lags behind the run. Wire the regen into the same hook that appends to `events.jsonl` (or call it from the lifecycle layer in `lib/lifecycle.py`). If regen is expensive, gate it behind a debounce — but staleness is the failure mode to avoid.
- [ ] Output sections (one screen, markdown):
  - **Header** — `run_id`, current status, repo, worktree, branch, created/updated timestamps.
  - **What changed** — files touched in the worktree, grouped by add / modify / delete. Pull from `diff-summary.md` if present; otherwise from `git diff --name-status` against `base_ref`.
  - **What was added** — high-level list of new capabilities / artifacts produced in this run (derived from `brief.md` scope + `implementation-summary.md` if present).
  - **Course corrections (addendum)** — every `BounceRequested` event in this run's `events.jsonl`, with `bounce_reason`, requester, and which state it bounced from. This is the change-request log.
  - **Timeline** — collapsed: one line per state transition (`draft → shaping → planning → …`), with timestamps. `CommandRun` / `ArtifactWritten` rolled up into counts per state, not listed individually.
- [ ] Slash command `/summary` — thin wrapper, defaults to the current run, prints `summary.md` inline.
- [ ] `--format json` for machine readers (same data, structured).
- [ ] Decision: `summary.md` lives inside the run directory (single source of truth, regenerated). Do **not** also append to `LOG.md` — `LOG.md` stays hand-curated.
- [ ] Test: assert that after a bounce → continue cycle, the addendum section lists the bounce reason and the summary's "what changed" reflects the post-bounce diff.

## 5. Automatic E2E testing

V1 has unit tests + integration tests that drive the CLI through the happy path / bounce / abandon. What's missing is a true end-to-end smoke that exercises the full LLM-bearing flow (`/shape`, `/plan`, `/validate`) against a real throwaway repo without a human in the loop.

- [ ] Define what "E2E" means here: one fixture repo + one canned `raw-idea.md` driven from `new-run` to `complete` with no manual prompts.
- [ ] Pick the harness. Options: a `scripts/e2e.sh` shell driver, a `tests/test_e2e.py` that subprocesses the CLI + a stub LLM, or a real Claude Code headless invocation. Default: shell driver that calls the CLI; LLM steps stubbed by writing canned artifact files (`brief.md`, `plan.md`, `review.md`, `qa/report.md`).
- [ ] Build a `tests/fixtures/e2e/` tree: throwaway repo seed, `raw-idea.md`, canned outputs for each LLM-bearing stage.
- [ ] Wire a `--stub-llm` (or env var `AGENT_WORKBENCH_STUB_LLM=1`) mode so `/shape`, `/plan`, `/validate` skip the model and copy fixture artifacts into the run directory. Slash command bodies stay unchanged; the Bash prefix branches on the flag.
- [ ] Assertions per stage: state advanced correctly, expected artifacts exist, `events.jsonl` contains the expected event types in order, `audit.md` renders.
- [ ] Run the E2E in CI on every push to a feature branch. Fail loudly on any unexpected event or state.
- [ ] Add a second E2E that exercises the **bounce loop** (validate → bounce → validate → complete) and a third for **abandon** at a random non-terminal state.
- [ ] Document how to add a new E2E scenario in `agent-workbench-live/tests/README.md`.

## 6. Context graph

A library of small, focused "context files" that the workbench's `AGENTS.md` (or per-stage prompts) link to with `@path/to/file.md`. Claude Code resolves `@`-imports lazily — the file's content only enters the model's context when it's actually relevant to the current task. Today the workbench has no such library, so every run re-derives basics like "use poetry, not pip" or "create a worktree before editing" from scratch (or worse, gets them wrong).

Goal: ship a `agent-workbench-live/context/` directory of opinionated, one-page-each guides, wired into `AGENTS.md` via `@context/<name>.md` references so the implementing agent loads them on demand.

- [ ] Create `agent-workbench-live/context/` and an index `context/README.md` that lists every file with a one-line description (so `AGENTS.md` can reference the index, not every file individually).
- [ ] Decide reference style. Default: `AGENTS.md` contains a "Context library" section that lists `@context/<name>.md` lines grouped by topic. Claude Code's import resolver will pull only the ones it deems relevant. Alternative: per-stage `.claude/commands/*.md` bodies embed the imports they need (`/plan` imports language guides, `/validate` imports the testing guide, etc.). Probably do both — global index in `AGENTS.md`, targeted imports in slash commands.
- [ ] Language guides — one file each, ~1 page, opinionated:
  - [ ] `context/python.md` — use **poetry** (not pip/uv/conda), `pyproject.toml` layout, `poetry add` / `poetry run`, virtualenv location, `poetry.lock` commits, `bin/pytest` if a repo has one, type hints + `ruff` defaults.
  - [ ] `context/javascript.md` — use **pnpm** (not npm/yarn/bun), `pnpm-workspace.yaml` for monorepos, `pnpm-lock.yaml` commits, `pnpm add` / `pnpm run`, `package.json` scripts as source of truth, no global installs, TypeScript over plain JS for new files.
  - [ ] `context/golang.md` — `go mod tidy` after dep changes, `go test ./...`, table-driven tests, `gofmt` / `goimports`, error wrapping (`fmt.Errorf("...: %w", err)`).
  - [ ] `context/ruby.md` — `bundle install` / `bundle exec`, `Gemfile.lock` commits, rspec layout, `rubocop` defaults.
- [ ] Workflow guides — same one-page format:
  - [ ] `context/git-commit.md` — commit message style (subject + body, imperative mood), one logical change per commit, never `--amend` published commits, never `--no-verify` without explicit user approval, HEREDOC for multi-line messages.
  - [ ] `context/git-worktrees.md` — when to use a worktree, `git worktree add` recipe, **always `pwd` + `git branch --show-current` before any git op in a worktree**, cleanup with `git worktree remove`, the `LOCAL_worktrees/` convention this repo uses.
  - [ ] `context/git-rebase.md` — when to rebase vs. merge, never rebase shared branches, conflict resolution, `git rebase --abort` as the escape hatch.
- [ ] Other common things worth a one-pager (suggested):
  - [ ] `context/pull-requests.md` — gh CLI recipe, title under 70 chars, body template (Summary / Test plan), draft vs. ready, never force-push to main.
  - [ ] `context/testing.md` — write the failing test first, smallest scope possible, parametrize for variation, no mocks at boundaries we don't own.
  - [ ] `context/secrets.md` — never commit `.env` / credentials, redact tokens in logs, use the repo's existing secret manager pattern.
  - [ ] `context/sql-migrations.md` — backwards-compatible migrations, expand-then-contract, NOT NULL with backfill, never drop columns in the same release that stops writing them.
  - [ ] `context/docker.md` — multi-stage builds, `.dockerignore` hygiene, pinned base images, no `latest` tags.
  - [ ] `context/shell.md` — `set -euo pipefail` in scripts, quote variables, `mktemp` for temp files, never `rm -rf $VAR` without a guard.
  - [ ] `context/dependency-bumps.md` — read the changelog, run the test suite, separate PR per ecosystem (don't mix pnpm + poetry in one PR).
  - [ ] `context/code-review.md` — what to flag (correctness, security, perf), what not to flag (style nits the formatter handles), how to phrase suggestions.
- [ ] Authoring rules for every context file:
  - [ ] One screen max (~50 lines). If it grows, split it.
  - [ ] Opinionated — prescribe one way, not three.
  - [ ] Include a 3-line "when this applies" header so the model can decide whether to load it.
  - [ ] Examples > prose. Show a command or snippet, not a paragraph.
- [ ] Test that imports actually fire: run a `/plan` for a Python repo, confirm the model references poetry-specific guidance without it being in the user prompt.
- [ ] Document the library in `AGENTS.md`: how to add a new context file, naming convention, when to inline vs. reference.
- [ ] (Stretch) `agent-workbench context list` — print the index. `agent-workbench context show <name>` — print a single file. Useful when debugging "why did the agent do X" — you can see exactly what guidance it had access to.
