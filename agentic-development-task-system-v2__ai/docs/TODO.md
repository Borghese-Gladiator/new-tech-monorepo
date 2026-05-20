# TODO

Next round of work after V1. Each section captures one idea — what it is, why we want it, and the concrete pieces to build.

**Renovate task workflow (originally §1) is complete** — all of 1a/1b/1c/1d/1e/1f/1g landed across four commits (`d1d8b44`, `d5ee45e`, `90a3daf`, and the §1g commit). Remaining work is renumbered below.

Order reflects priority: worktree naming is the small, isolated warm-up. Then board, summary, E2E, context graph.

---

## 1. Better worktree name

Today `worktree_name` defaults to the slug of the brief title — fine for short titles but loses information for longer ones, and there's no signal of *what stage* the work is in or *which repo* it targets when you're staring at a `worktrees/` directory.

- [ ] Audit current naming: `worktrees/<repo_name>/<slug>`. Document the failure modes (collisions when two runs share a slug; opaque names when slugs are truncated; no date hint).
- [ ] Decide on a new template. Candidate: `<YYYYMMDD>__<slug>` (matches the existing `LOCAL_worktrees` convention this repo uses — see `202605_agent_workbench_v2`). Alternative: `<run_id>` directly (already date-prefixed + slug, guaranteed unique).
- [ ] Update `agent-workbench.yaml.defaults.worktree_name_template` and the resolver in `lib/run_ids.py`.
- [ ] Decide whether `branch_name` follows the same pattern. Current: `agent/<worktree_name>`. Probably stays — but verify the new template doesn't break git's branch name rules.
- [ ] Migration story for existing in-flight runs: don't rename them. New template applies only to runs created after the change. Add a one-line note in `lifecycle.md`.
- [ ] Update integration tests that assert on worktree paths.
- [ ] Update `AGENTS.md` and `README.md` examples.
- [ ] (Stretch) Allow the user to override per-run via `new-run --worktree-name <name>` — already supported; just make sure the slug-sanitizer doesn't strip the new template's separators (`_`, double-underscore).

## 2. Task board

Right now run state is scattered across `runs/<run_id>/metadata.yaml` files. To see what's in flight you have to `agent-workbench list` and squint. A task board surfaces all runs grouped by lifecycle state so humans can see queue depth and what needs attention.

- [ ] Decide format. Default: terminal-rendered Kanban (`agent-workbench board`) with one column per state (`draft`, `shaping`, `planning`, `ready`, `building`, `validating`, `followups`, `human_review`, `done`, `abandoned`). Stretch: an HTML render written to `runs/_board.html` for browser viewing.
- [ ] Add `agent-workbench board` subcommand. Reads every `runs/*/metadata.yaml`, groups by status, prints columns with `run_id`, age (since `updated_at`), `repo_name`, branch.
- [ ] Highlight runs that have been in `human_review` for more than N hours (configurable in `agent-workbench.yaml.board.stale_human_review_hours`).
- [ ] Hide terminal states by default; `--all` includes `done` and `abandoned`.
- [ ] Slash command `/board` — thin wrapper.
- [ ] (Stretch) `agent-workbench board --html <path>` writes a single self-contained HTML file. No server, no JS framework — just a static dump regenerated on demand.
- [ ] (Stretch) Per-run "blocker" field in metadata so the board can show *why* a run is stalled in `human_review` (e.g., "waiting on QA env").

## 3. Activity log summary

Per-run, human-readable rollup of what a single run produced — not a cross-run digest. Goal: open one file and see at a glance *what changed* and *what was added* in that run, including any mid-flight course corrections from `/bounce`. `events.jsonl` is the source of truth but it's noisy (every `CommandRun` and `ArtifactWritten`); `audit.md` is a chronological dump. Neither answers "what did this run actually do?" in one screen.

- [ ] Add `agent-workbench summary <run_id>` subcommand. Default target: the run identified by `<run_id>`; with no arg, the most recently updated run. Writes (or refreshes) `runs/<run_id>/summary.md`.
- [ ] **Keep it current.** The summary must be regenerated on every state transition and every artifact write so it never lags behind the run. Wire the regen into the same hook that appends to `events.jsonl` (or call it from the lifecycle layer in `lib/lifecycle.py`). If regen is expensive, gate it behind a debounce — but staleness is the failure mode to avoid.
- [ ] Output sections (one screen, markdown):
  - **Header** — `run_id`, current status, repo, worktree, branch, created/updated timestamps.
  - **What changed** — files touched in the worktree, grouped by add / modify / delete. Pull from `stages/building/build.md` if present; otherwise from `git diff --name-status` against `base_ref`.
  - **What was added** — high-level list of new capabilities / artifacts produced in this run (derived from `stages/shaping/brief.md` scope + `stages/building/build.md` if present).
  - **Course corrections (addendum)** — every `BounceRequested` event in this run's `events.jsonl`, with `bounce_reason`, requester, and which state it bounced from. This is the change-request log.
  - **Timeline** — collapsed: one line per state transition (`draft → shaping → planning → …`), with timestamps. `CommandRun` / `ArtifactWritten` rolled up into counts per state, not listed individually.
- [ ] Slash command `/summary` — thin wrapper, defaults to the current run, prints `summary.md` inline.
- [ ] `--format json` for machine readers (same data, structured).
- [ ] Decision: `summary.md` lives inside the run directory (single source of truth, regenerated). Do **not** also append to `LOG.md` — `LOG.md` stays hand-curated.
- [ ] Test: assert that after a bounce → continue cycle, the addendum section lists the bounce reason and the summary's "what changed" reflects the post-bounce diff.

## 4. Automatic E2E testing

V1 has unit tests + integration tests that drive the CLI through the happy path / bounce / abandon. What's missing is a true end-to-end smoke that exercises the full LLM-bearing flow (`/shape`, `/plan`, `/validate`, `/followups`) against a real throwaway repo without a human in the loop.

- [ ] Define what "E2E" means here: one fixture repo + one canned `raw-idea.md` driven from `new-run` to `complete` with no manual prompts.
- [ ] Pick the harness. Options: a `scripts/e2e.sh` shell driver, a `tests/test_e2e.py` that subprocesses the CLI + a stub LLM, or a real Claude Code headless invocation. Default: shell driver that calls the CLI; LLM steps stubbed by writing canned artifact files (`brief.md`, `plan.md`, `build.md`, `review.md`, `qa/report.md`, `HUMAN_REVIEW.md`, `follow-ups.md`).
- [ ] Build a `tests/fixtures/e2e/` tree: throwaway repo seed, `raw-idea.md`, canned outputs for each LLM-bearing stage.
- [ ] Wire a `--stub-llm` (or env var `AGENT_WORKBENCH_STUB_LLM=1`) mode so `/shape`, `/plan`, `/validate`, `/followups` skip the model and copy fixture artifacts into the run directory. Slash command bodies stay unchanged; the Bash prefix branches on the flag.
- [ ] Assertions per stage: state advanced correctly, expected artifacts exist, `events.jsonl` contains the expected event types in order, `audit.md` renders.
- [ ] Run the E2E in CI on every push to a feature branch. Fail loudly on any unexpected event or state.
- [ ] Add a second E2E that exercises the **bounce loop** (validate → followups → bounce → validate → followups → complete) and a third for **abandon** at a random non-terminal state.
- [ ] Document how to add a new E2E scenario in `agent-workbench-live/tests/README.md`.

## 5. Context graph

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

## 6. Followup spawn (TODO §1f stretch, deferred)

The pass-3 Renovate work landed the `followups` stage but **deliberately did not implement** the `agent-workbench followup spawn` command. That command — create a new `draft` run pre-populated from a chosen mini-brief in a prior run's `follow-ups.md` — is the natural next step now that follow-ups are first-class.

- [ ] Add `agent-workbench followup spawn <run_id> <n>` (or `--title <substr>`). Reads `runs/<run_id>/stages/followups/follow-ups.md`, picks entry N (1-indexed) or the first entry whose title matches, derives a `raw-idea.md` from `motivation` + `suggested_scope`, runs the equivalent of `new-run` against the same repo as the source run.
- [ ] Decision: does the spawned run inherit the source run's `repo-path` automatically? Default yes; override via `--repo-path`.
- [ ] Slash command `/followup-spawn` — thin wrapper.
- [ ] Event: emit a `FollowupSpawned` event in the *source* run's events.jsonl noting which entry was picked + the new run_id (so spawn lineage is queryable).
- [ ] Test: spawn from a recorded entry → new run lands in `draft` with correct raw-idea.
