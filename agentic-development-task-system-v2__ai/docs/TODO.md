# TODO

Next round of work after V1. Each section captures one idea — what it is, why we want it, and the concrete pieces to build.

**Completed work, summarised at the top so this file shrinks over time:**

- ✅ Renovate task workflow (originally §1; 1a–1g across four commits `d1d8b44`, `d5ee45e`, `90a3daf`, `827a06a`).
- ✅ Better worktree name (originally §2 after renumbering; merged into `202605_agent_workbench_v2` from `agent/better-worktree-name-template`).
- ✅ Numbered stage directories (originally §1 after this renumbering; `stages/1_draft/`, `2_shaping/`, …). Same dogfood pass cleared four follow-ups: scope_check path-prefix matching, `extract_run_date` unit tests, `show` rendering the `build:` block, multi-line ASM/DR body parsing.
- ⚠️ Task board v0 (originally §1, commit `0fe9214`) — shipped a simple `agent-workbench board` / `/board` that prints a static text Kanban grouped by lifecycle state. Superseded by the live Textual TUI below (`f10b6d8`); the v0 contract survives as the `--static` fallback path.
- ✅ Live task board — Textual TUI (originally §1 after renumbering, commit `f10b6d8`). `agent-workbench board` launches a full-screen Textual app over `runs/` with a watchdog file-watcher + 1Hz fallback timer; cards re-render on every `metadata.yaml` / `events.jsonl` change. Status-aware card bodies, loud-card highlighting, `--static` / `--compact` / `--all` / `--status` knobs. `textual` + `watchdog` shipped as a `[board]` optional-deps group (`requirements-board.txt`) — core CLI stays stdlib-only.
- ✅ Live board card attributes (originally §2 after renumbering, commits `549c9aa` + `445f3cd` + `52926b5`). Eleven on-disk fields that the anemic v1 card body never surfaced now render status-aware: lifecycle state badge, scope kind, idle/`● live` signal, AC coverage (parsed from build.md), git diff shortstat (cached on `(run_id, updated_at)`), avg iteration time, bounce origin, followup category breakdown, repo-path tail, terminal-card `accepted_by`/`abandoned_reason`, worktree-existence flag, tests-recorded age. Dogfood (`445f3cd`, run `2026-05-22-s2-attrs`) drove a fresh `repair`-scope run through every column and surfaced one renderer bug — the static path's `human_review` branch missed the followups-category breakdown — fixed inline and locked in by a regression test (`52926b5`).
- ✅ Live board — UX polish on the card layout (originally §1 after renumbering). Card now renders as five bands separated by `─` rules: title (slug bright + dim date prefix + state badge + scope + `● live`), meta (age-in-stage · age since update · total · repo · branch — dim), body (status-aware progress with severity-led reason), events (`[mm:ss ago] EventType detail`, fixed-width timestamp column), files (labelled `run` / `wt` lines, `$HOME → ~`, workbench root → `…`, off by default; `--verbose` opts in). Loudness graded: warning (`⚠`, yellow border) for known issues / recent error / worktree missing; blocking (`✕`, red border) for failing tests / builder-gave-up / stale `human_review`. Reason rendered as the first body line (`✕ tests failing`, `⚠ 2 known issues`). Each column gains a one-line subtitle pulled from `COLUMN_SUBTITLES` in `lib/board/source.py`. Twenty-four new tests across severity classification, path abbreviation, band content selection, event-timestamp format, the `--verbose` knob, and the column subtitle line. Suite is 188/188 green.
- ✅ Automatic E2E testing (originally §1 after renumbering). New `lib/stub_llm.py` + `AGENT_WORKBENCH_STUB_LLM` env-var mode lets the four LLM-bearing CLI subcommands (`shape`, `plan`, `validate`, `followups`) copy canned artifacts from a fixture directory in lieu of authoring them with a model. Slash command bodies stay unchanged — the hook fires from inside each `--init` Bash step. Two fixture sets shipped under `tests/fixtures/e2e/`: `happy/` (single-pass run to `done`) and `bounce_pass1/` + `bounce_pass2/` (request-changes review on pass 1, accept on pass 2). New `tests/test_e2e.py` drives three scenarios: `TestE2EHappyPath` (full `new-run → complete`), `TestE2EBounceLoop` (full happy path + bounce + re-validate + complete, asserts archived `-v1` outputs and event-log counts per transition), and `TestE2EAbandon` (`*->abandoned` from draft / shaping / building). `tests/README.md` documents how to add a scenario. Five new tests; suite is 193/193 green.
- ✅ Audit unit tests for duplication (originally §3, commit `<PENDING>`; run `2026-05-22-audit-unit-tests-for-duplication`). Suite shrunk from 193 → 134 (−59 tests, −30.6%) by folding methods that share preconditions into one test method per group with a `for label, … in cases:` loop and `msg=label` for per-row diagnosis (the user's CLAUDE.md "App Testing Rules" pattern). Biggest reductions: `test_scope_check.py` 16→2 (`TestExtractExpectedFiles` 6→1, `TestDetectCreep` 10→1), `test_cmd_board.py` 35→22 (`TestSeverityClassification` 8→1, `TestPathAbbreviation` 4→1, three severity-marker tests in `TestStaticCardBands` 3→1), `test_doc_claims.py` 10→2. No production code changed; `TestStaticCardStack` (regression-locked per `52926b5`) and `test_e2e.py` scenarios are byte-identical to pre-prune. Plan's original "parametrize-as-merge" approach was discarded mid-build because pytest counts each parametrize case as a test — the count only drops when multiple methods collapse into one method with multiple assertions inside.

Order reflects priority: context graph, followup spawn.

---

## 1. Context Graph

Stop agents from repeatedly rediscovering project conventions (package manager, testing, Git safety, PR rules, infra/migration safety, bug triage) by adding a small opinionated context library under `agent-workbench-live/context/`. Agents lazy-import individual files via `@context/path/to/file.md`; slash commands compose targeted imports instead of duplicating instructions inline.

**Design principles**

- Context files are conventions/safety/defaults, not workflows. Workflows belong in `.claude/commands/*`, which compose context files.
- One concern per file, one screen max (~50 lines), example-heavy over prose, one default way ("it depends" is a smell).
- Organized by concern: `meta`, `git`, `languages`, `infra`, `diagnostics`. No `context/workflows/` directory.
- Every file follows the same template: `Applies when:` / `Do:` / `Do not:` / `Commands:`.

**Directory layout**

```text
agent-workbench-live/context/
  README.md
  meta/{context-authoring,repo-discovery,risk-and-approval}.md
  git/{commit,worktrees,draft-pr}.md
  languages/python/{setup,dependencies,testing,quality}.md
  languages/javascript-typescript/{setup,dependencies,testing,quality}.md
  languages/go/{setup,dependencies,testing,quality}.md
  infra/{secrets,shell,docker,ci,sql-migrations}.md
  diagnostics/sentry-bug-triage.md
```

**Tasks**

- [ ] Inspect existing `AGENTS.md`, `CLAUDE.md`, `.claude/commands/*`, and repo conventions before authoring; preserve any defaults that already differ from the generic ones below.
- [ ] Create the normalized directory tree under `agent-workbench-live/context/`.
- [ ] **Meta** — `context-authoring.md` (naming, one-screen rule, when to split, examples > prose, when to inline vs. import, avoid workflow duplication); `repo-discovery.md` (detect language / package manager / test runner / CI / lint+format+typecheck commands; prefer repo-local scripts; example commands: `pwd`, `ls`, `find . -maxdepth 3 -name pyproject.toml -o -name package.json -o -name go.mod`, `find . -maxdepth 3 -name AGENTS.md -o -name CLAUDE.md -o -name Makefile`); `risk-and-approval.md` (ask before force-push / destructive deletes / destructive migrations; classify low/medium/high risk; prefer reversible operations).
- [ ] **Git** — intent-oriented, not one file per porcelain command. `commit.md` (one logical change per commit, imperative ≤70-char subject, HEREDOC for multiline, never `--no-verify` without approval, never amend published commits unless approved). `worktrees.md` (`LOCAL_worktrees/` convention, cleanup expectations, always `pwd` + `git branch --show-current` + `git status --short` before Git ops). `draft-pr.md` (inspect diff, run validation + tests before PR, draft PRs for incomplete work, body = Summary + Test plan, never force-push to `main`).
- [ ] **Languages** — same `setup` / `dependencies` / `testing` / `quality` quartet for each. **Python**: Poetry default; `bin/pytest` if present else `poetry run pytest`; `ruff check`, `ruff format --check`, `mypy`, `pytest`. **JS/TS** (directory `javascript-typescript`): Yarn default, no global installs, TS-first; `yarn lint` / `typecheck` / `build` / `test`; avoid `any`. **Go**: Go modules, `gofmt`, `go test ./...`, wrap errors with `%w`, small interfaces, no mutable package globals.
- [ ] **Infra** — `secrets.md` (never commit secrets or `.env`, redact tokens in logs, no creds in PRs/issues/tests); `shell.md` (`set -euo pipefail`, quote variables, `mktemp`, guard destructive deletes); `docker.md` (multi-stage builds, `.dockerignore`, pinned bases, never `latest`, no baked secrets); `ci.md` (mirror CI checks locally, prefer repo scripts, never weaken CI to pass, document skipped checks); `sql-migrations.md` (backwards-compatible, expand-then-contract, backfill before `NOT NULL`, avoid long locks, never drop columns in the same release that stops writes).
- [ ] **Diagnostics** — `sentry-bug-triage.md`: tool-agnostic (no Sentry CLI/API assumptions). Identify project/env/release, inspect frequency/impact, find first in-repo stack frame, correlate with recent deploys / dependency bumps, add regression tests after root-cause, never log sensitive data, never close issues without rationale.
- [ ] Create `context/README.md` — primary discovery entrypoint. Lists every file with one-line description + `@context/...` import path, organized by section.
- [ ] Wire `AGENTS.md`: add a section that references `@context/README.md`, explains lazy loading + composition by commands, does **not** inline the file list.
- [ ] Wire `CLAUDE.md`: explain Claude Code's lazy `@context/...` resolution, prefer focused imports, reference `@context/README.md` + `@context/meta/repo-discovery.md` + `@context/meta/risk-and-approval.md`.
- [ ] Update existing `.claude/commands/*` files to compose targeted imports (examples: validation → `@context/meta/repo-discovery.md` + `@context/git/draft-pr.md` + `@context/infra/ci.md`; Python implementation → `@context/languages/python/testing.md` + `@context/languages/python/quality.md` + `@context/git/worktrees.md`; Sentry triage → `@context/diagnostics/sentry-bug-triage.md` + `@context/git/draft-pr.md` + `@context/meta/risk-and-approval.md`).
- [ ] Run formatting / lint / tests; confirm acceptance: every required file exists and follows the template, every file ≤~50 lines, no `context/workflows/` directory, `README.md` indexes every file, `AGENTS.md` + `CLAUDE.md` reference the library, relevant commands use targeted imports, existing repo conventions preserved over generic defaults.

**Non-goals**

Large workflow documents; one file per Git command; duplicated guidance; long-form architecture docs; tutorials; assuming tools the repo doesn't already use; Sentry-specific API integrations.

## 2. Followup spawn (TODO §1f stretch, deferred)

The pass-3 Renovate work landed the `followups` stage but **deliberately did not implement** the `agent-workbench followup spawn` command. That command — create a new `draft` run pre-populated from a chosen mini-brief in a prior run's `follow-ups.md` — is the natural next step now that follow-ups are first-class.

- [ ] Add `agent-workbench followup spawn <run_id> <n>` (or `--title <substr>`). Reads `runs/<run_id>/stages/followups/follow-ups.md`, picks entry N (1-indexed) or the first entry whose title matches, derives a `raw-idea.md` from `motivation` + `suggested_scope`, runs the equivalent of `new-run` against the same repo as the source run.
- [ ] Decision: does the spawned run inherit the source run's `repo-path` automatically? Default yes; override via `--repo-path`.
- [ ] Slash command `/followup-spawn` — thin wrapper.
- [ ] Event: emit a `FollowupSpawned` event in the *source* run's events.jsonl noting which entry was picked + the new run_id (so spawn lineage is queryable).
- [ ] Test: spawn from a recorded entry → new run lands in `draft` with correct raw-idea.
