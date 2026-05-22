# TODO

Next round of work after V1. Each section captures one idea — what it is, why we want it, and the concrete pieces to build.

**Completed work, summarised at the top so this file shrinks over time:**

- ✅ Renovate task workflow (originally §1; 1a–1g across four commits `d1d8b44`, `d5ee45e`, `90a3daf`, `827a06a`).
- ✅ Better worktree name (originally §2 after renumbering; merged into `202605_agent_workbench_v2` from `agent/better-worktree-name-template`).
- ✅ Numbered stage directories (originally §1 after this renumbering; `stages/1_draft/`, `2_shaping/`, …). Same dogfood pass cleared four follow-ups: scope_check path-prefix matching, `extract_run_date` unit tests, `show` rendering the `build:` block, multi-line ASM/DR body parsing.
- ⚠️ Task board v0 (originally §1, commit `0fe9214`) — shipped a simple `agent-workbench board` / `/board` that prints a static text Kanban grouped by lifecycle state. This is a placeholder; the real implementation is §1 below (live Textual TUI directly on top of `runs/`). Keep the v0 binary working until §1 lands so `/board` doesn't break.

Order reflects priority: live task board, E2E, context graph, followup spawn.

---

## 1. Live task board — Textual TUI directly on top of `runs/`

The v0 task board is a static one-shot text dump: you run `agent-workbench board`, you get a snapshot, you re-run to see fresh state. That's wrong for the workflow. While a run is in flight — `building` writing artifacts, `validating` appending review.md sections, `followups` finalizing — we want to **see it happen** in a live terminal dashboard without re-running anything.

This is **project-specific**, not a reusable library:

- Lives in this repo, integrated directly with `agent-workbench-live/`.
- Reads the workbench's existing on-disk state (`runs/<id>/metadata.yaml`, `events.jsonl`, stage files) — that **is** the source of truth.
- No public Python API to expose, no library packaging, no framework-agnostic abstractions, no event-bus emitters that workbench code has to call. The board is a renderer; the workbench writes files as it already does.
- **Not interactive.** It's a live dashboard, like `htop`. Keyboard input is limited to `q` (quit). No filters, no command palette, no pause — if you want a different view, restart with a CLI flag.
- **Always shows current state.** This is the bar to clear: every visible field must reflect what's on disk right now, not what was on disk when the board started.

### Goal

Run `agent-workbench board` (or `/board`) and get a full-screen Textual TUI that auto-refreshes and renders every run grouped into a Kanban by lifecycle state. Leave it open in a pane while a run executes; the board updates as files change.

### Stack

- **Textual** for the full-screen TUI + auto-refresh loop.
- **Rich** for tables, status badges, progress bars, timestamps — used via Textual widgets.
- Both added as a new optional dep group (`board`) on the workbench, so the core CLI keeps stdlib-only as a hard requirement and `agent-workbench board` is the one command that pulls in third-party packages.

### Liveness — the part that has to actually work

The v0 board misses the point because it's a snapshot. Liveness is the whole feature. Architecture decisions follow from that:

1. **Source of truth = the filesystem.** No in-memory caches between Textual and `runs/`. Every refresh re-reads metadata + the relevant tail of `events.jsonl`. If the file changed, the board changed.
2. **Refresh strategy.** Two layers:
   - **`watchdog`-based file watcher** on `runs/` for low-latency updates. Each `metadata.yaml` write or `events.jsonl` append triggers a refresh of the affected run only — not the whole board.
   - **Fallback timer** at ~1 Hz so the board never gets stuck if `watchdog` misses an event (e.g., on a filesystem that doesn't deliver inotify-equivalent events). The timer also drives "age since updated_at" tickers so the visible age clock keeps moving even when nothing is changing on disk.
3. **Atomic reads.** The workbench already writes metadata.yaml atomically (`.tmp` → rename). The board reads via the same `metadata.load` helper, so partial-write races are not a concern. For `events.jsonl`, the board tails by seek-to-known-offset; if the file shrank (run reset?), reset the offset and re-read.
4. **Per-run state is rebuilt from disk every cycle, not maintained as a stateful in-memory model.** This is the bargain for guaranteed correctness: cheap to be wrong, expensive to be subtly stale. The on-disk dataset is small (tens of runs at most for this project), so re-reading everything on each tick is fine.
5. **No subprocess shells from inside the render loop.** Anything expensive (e.g., `git diff` for change-count) is computed lazily on demand or cached with a short TTL keyed on `(run_id, updated_at)` so a re-read of the same metadata doesn't re-run git.

### Architecture (revised for this project)

This is materially simpler than the previous library plan because we don't need an event bus, a public API, or producer/consumer separation — the workbench is already the producer (it writes files), and the board is the only consumer.

```
agent-workbench board (cmd_board.py)
        │
        ▼
┌────────────────────────────┐
│ lib/board/source.py        │  Reads runs/<id>/metadata.yaml + events.jsonl
│   list_runs_with_state()   │  Computes derived fields (age, blocked_on,
│                            │  iteration count, last event summary, etc.)
└────────────┬───────────────┘
             ▼
┌────────────────────────────┐
│ lib/board/snapshot.py      │  Pure dataclass: BoardSnapshot, RunCard,
│   BoardSnapshot.build()    │  KanbanColumn. Built from source on each tick.
└────────────┬───────────────┘
             ▼
┌────────────────────────────┐
│ lib/board/app.py           │  Textual App. One Screen, fixed widgets.
│   AgentBoardApp            │  Re-renders from a fresh snapshot on every
│                            │  watcher event + 1Hz fallback timer.
└────────────────────────────┘
```

Files live under `agent-workbench-live/lib/board/`. No `src/` layout, no `pyproject.toml`, no separate package. The v0 `cmd_board.py` gets rewritten to launch this Textual app; the existing test (`tests/test_cmd_board.py`) is replaced with snapshot-builder tests that don't require a TTY.

### Per-task (per-run) metadata to show

The card-per-run model is right; the v0 card was anemic (just run_id, age, repo, branch). Brainstormed additions, grouped by why they matter at triage time:

**Identity & location** — already on the v0 card, keep:
- `run_id`
- `repo_name`
- `branch_name`
- `worktree_name` (different from branch; useful when worktree was renamed)

**Lifecycle position** — what tells the human "what is this thing doing right now":
- current `status` (column it lives in)
- `age` since `updated_at` (live ticker)
- `age` since `created_at` (total run age; useful when something has been crawling for days)
- `time_in_current_stage` (computed from the last `TransitionApplied` event for this run — distinct from `updated_at`, because an in-stage artifact write also touches `updated_at`)

**Progress signals inside a stage** — the part v0 has nothing on:
- For `building`: `build.iterations` / `build.max_iterations` (e.g., `2/5` with a progress bar). This is already in metadata under `build:`.
- For `building`: presence of `stages/4_building/build.md` yet? (file exists → builder has started writing)
- For `validating`: tests_passed (✓/✗/?), known_issues_count, review_completed, qa_completed (already in `validation:` block).
- For `validating`: presence of `Documentation claims` / `Scope creep check` sections in review.md (flags that the deterministic checks fired and what they found, even before the reviewer signs off).
- For `followups`: count of entries in follow-ups.md, count tagged `no_followups`.

**Health flags** — the things that should make a card visually loud:
- Stale `human_review` (already in v0 — keep).
- `build.exit_reason == "max_iterations"` — the builder gave up; reviewer needs to look.
- `validation.tests_passed == false` — failing tests.
- `validation.known_issues_count > 0` — known issues recorded.
- Recent `BounceRequested` event — show "bounced from X" with a bounce count.
- Recent `Error` / failed `CommandRun` events in `events.jsonl` since the last transition.

**Last activity (the live bit)** — gives the strongest "this is moving" signal:
- Last 3 event types from `events.jsonl`, with timestamps. e.g., `ArtifactWritten review.md · 4s ago`, `DocClaimsVerified · 12s ago`, `ScopeCreepChecked · 18s ago`.
- "Currently writing" hint: if the last event is `ArtifactWritten` within the last few seconds, show a subtle indicator on the card.

**Audit links** — printed at the bottom of the card, no interaction:
- absolute path to the run dir (so user can `cd` to it in another pane).
- absolute path to the worktree (so user can open the diff in another pane).

Not every field on every card. Card layout is **status-aware**: a `draft` card shows almost nothing (just identity + age), while a `building` card prioritizes iteration progress + last events, and a `validating` card prioritizes the validation flags.

### Kanban layout (Textual)

Each lifecycle state is a column. Columns are widgets, cards are widgets, the board scrolls.

```
┌─ AGENT BOARD ───────────────────────────────────────────────── 19:42:11 ─┐
│                                                                          │
│  draft (1)    shaping (0)   planning (2)   ready (0)   building (1)  …   │
│  ──────────   ───────────   ────────────   ─────────   ────────────      │
│  ┌────────┐                 ┌─────────┐                ┌────────────┐    │
│  │ 2026-  │                 │ 2026-…  │                │ 2026-…     │    │
│  │ 05-21- │                 │ better- │                │ board-tui  │    │
│  │ tui    │                 │ worktree│                │            │    │
│  │ 0m     │                 │ 1h      │                │ 4m  in 4_  │    │
│  │ repo:… │                 │         │                │ building   │    │
│  │ branch │                 │         │                │ build 2/5  │    │
│  │        │                 │         │                │ [████░░░░] │    │
│  │        │                 │         │                │ events:    │    │
│  │        │                 │         │                │   ArtfctW… │    │
│  │        │                 │         │                │   CmdRun…  │    │
│  └────────┘                 └─────────┘                └────────────┘    │
│                                                                          │
│  …  validating (1)   followups (0)   human_review (1)   done (1)*       │
│      ────────────   ────────────    ────────────────   ─────────         │
│      ┌──────────┐                   ┌──────────────┐   (hidden — pass    │
│      │ 2026-…   │                   │ ! 2026-05-18 │    --all)           │
│      │ qa ✓     │                   │ -poker       │                     │
│      │ rev ✗    │                   │ stale 3d     │                     │
│      │ creep!   │                   │              │                     │
│      └──────────┘                   └──────────────┘                     │
│                                                                          │
└──────── q quit · auto-refresh on file change ────────────────────────────┘
```

Layout properties:

- Columns laid out left-to-right in canonical order (`draft, shaping, planning, ready, building, validating, followups, human_review`, plus `done`/`abandoned` when `--all`).
- Column headers show state name + count + a one-character marker if the column has any "loud" cards (e.g., a stale or failing run).
- Cards stack vertically within a column.
- If a column overflows the visible height, the column gets its own scroll. The whole board doesn't scroll horizontally — Textual reflows columns to fit the terminal width, dropping empty columns first when space is tight (a `draft (0)` column can collapse to a thin header strip).
- Color: status badges per state, red bar on the left edge of any "loud" card (stale, failing tests, max-iterations builder, scope creep flagged), no color on a healthy card.
- Compact mode: cards collapse to one-liner (run_id + age + key flag) when `--compact` is passed or terminal is narrower than a threshold.
- A footer shows: total run count, current local time, "auto-refresh: file-watch + 1Hz fallback", and the `q` shortcut.

### Out of scope (explicit non-goals)

- Interactivity beyond `q`. No drilling into a card. If the user wants details, use `agent-workbench show <run_id>` or open the run dir in another pane.
- Mutations from the TUI (no "advance state", no "abandon").
- Driving the board from anywhere other than the local `runs/` directory.
- HTML / web rendering. If we ever need a non-terminal view, do it as a separate render path on top of the same `BoardSnapshot`.
- Cross-machine views, syncing, or a daemon.

### Implementation order

- [x] Add `textual` + `watchdog` to a new `[board]` optional-deps group in `agent-workbench-live/` (still stdlib-only by default). — shipped as `agent-workbench-live/requirements-board.txt`; README updated.
- [x] Build `lib/board/source.py` — pure-function readers that produce `RunSnapshot` dataclasses from `metadata.yaml` + a configurable tail of `events.jsonl`. Includes derived fields (age, time-in-stage, last-3-events, build-progress, health flags). No Textual import.
- [x] Build `lib/board/snapshot.py` — `BoardSnapshot.build(cfg)` walks runs/, groups by status, returns a frozen snapshot ready for rendering.
- [x] Unit tests against snapshot.py: seed fake `runs/` trees (same pattern as the v0 tests), assert health flags, progress fields, last-events list, stage-aware card content. — `tests/test_board_snapshot.py`, 17 cases.
- [x] Build `lib/board/app.py` — Textual app. One screen, fixed column row + footer. Driven by a `watchdog` observer on `runs/` + 1 Hz fallback `set_interval`. Each refresh: rebuild snapshot, swap into the column widgets.
- [x] Rewrite `lib/cli/cmd_board.py` so it imports lazily (`from lib.board import app`) and launches the Textual app. Keep the existing CLI flags (`--all`, `--status`) and add `--compact`. Preserve the static text output behind `--static` so headless / CI usage still works.
- [x] Update `/board` slash command doc to describe the new live behavior.
- [x] Smoke test plan: start `agent-workbench board` in one pane; drive a fresh run through `new-run` → `shape --init` → … in another pane; visually confirm cards move columns and "last events" updates in real time without the user pressing anything. — verified in-process with `app.run_test()` pilot: dropped a run on disk while the app was mounted; watchdog fired; the building column rendered the new card without input.
- [x] Drop the `tests/test_cmd_board.py` rendering-format assertions that no longer apply; keep the format-age + grouping tests by retargeting them at `lib/board/snapshot.py`. — `format_age` + grouping live in `tests/test_board_snapshot.py`; `tests/test_cmd_board.py` now exercises the `--static` fallback path.

## 2. Automatic E2E testing

V1 has unit tests + integration tests that drive the CLI through the happy path / bounce / abandon. What's missing is a true end-to-end smoke that exercises the full LLM-bearing flow (`/shape`, `/plan`, `/validate`, `/followups`) against a real throwaway repo without a human in the loop.

- [ ] Define what "E2E" means here: one fixture repo + one canned `raw-idea.md` driven from `new-run` to `complete` with no manual prompts.
- [ ] Pick the harness. Options: a `scripts/e2e.sh` shell driver, a `tests/test_e2e.py` that subprocesses the CLI + a stub LLM, or a real Claude Code headless invocation. Default: shell driver that calls the CLI; LLM steps stubbed by writing canned artifact files (`brief.md`, `plan.md`, `build.md`, `review.md`, `qa/report.md`, `HUMAN_REVIEW.md`, `follow-ups.md`).
- [ ] Build a `tests/fixtures/e2e/` tree: throwaway repo seed, `raw-idea.md`, canned outputs for each LLM-bearing stage.
- [ ] Wire a `--stub-llm` (or env var `AGENT_WORKBENCH_STUB_LLM=1`) mode so `/shape`, `/plan`, `/validate`, `/followups` skip the model and copy fixture artifacts into the run directory. Slash command bodies stay unchanged; the Bash prefix branches on the flag.
- [ ] Assertions per stage: state advanced correctly, expected artifacts exist, `events.jsonl` contains the expected event types in order, `audit.md` renders.
- [ ] Run the E2E in CI on every push to a feature branch. Fail loudly on any unexpected event or state.
- [ ] Add a second E2E that exercises the **bounce loop** (validate → followups → bounce → validate → followups → complete) and a third for **abandon** at a random non-terminal state.
- [ ] Document how to add a new E2E scenario in `agent-workbench-live/tests/README.md`.

## 3. Context graph

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

## 4. Followup spawn (TODO §1f stretch, deferred)

The pass-3 Renovate work landed the `followups` stage but **deliberately did not implement** the `agent-workbench followup spawn` command. That command — create a new `draft` run pre-populated from a chosen mini-brief in a prior run's `follow-ups.md` — is the natural next step now that follow-ups are first-class.

- [ ] Add `agent-workbench followup spawn <run_id> <n>` (or `--title <substr>`). Reads `runs/<run_id>/stages/followups/follow-ups.md`, picks entry N (1-indexed) or the first entry whose title matches, derives a `raw-idea.md` from `motivation` + `suggested_scope`, runs the equivalent of `new-run` against the same repo as the source run.
- [ ] Decision: does the spawned run inherit the source run's `repo-path` automatically? Default yes; override via `--repo-path`.
- [ ] Slash command `/followup-spawn` — thin wrapper.
- [ ] Event: emit a `FollowupSpawned` event in the *source* run's events.jsonl noting which entry was picked + the new run_id (so spawn lineage is queryable).
- [ ] Test: spawn from a recorded entry → new run lands in `draft` with correct raw-idea.
