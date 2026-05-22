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

Order reflects priority: E2E, context graph, followup spawn.

---

## 1. Automatic E2E testing

V1 has unit tests + integration tests that drive the CLI through the happy path / bounce / abandon. What's missing is a true end-to-end smoke that exercises the full LLM-bearing flow (`/shape`, `/plan`, `/validate`, `/followups`) against a real throwaway repo without a human in the loop.

- [ ] Define what "E2E" means here: one fixture repo + one canned `raw-idea.md` driven from `new-run` to `complete` with no manual prompts.
- [ ] Pick the harness. Options: a `scripts/e2e.sh` shell driver, a `tests/test_e2e.py` that subprocesses the CLI + a stub LLM, or a real Claude Code headless invocation. Default: shell driver that calls the CLI; LLM steps stubbed by writing canned artifact files (`brief.md`, `plan.md`, `build.md`, `review.md`, `qa/report.md`, `HUMAN_REVIEW.md`, `follow-ups.md`).
- [ ] Build a `tests/fixtures/e2e/` tree: throwaway repo seed, `raw-idea.md`, canned outputs for each LLM-bearing stage.
- [ ] Wire a `--stub-llm` (or env var `AGENT_WORKBENCH_STUB_LLM=1`) mode so `/shape`, `/plan`, `/validate`, `/followups` skip the model and copy fixture artifacts into the run directory. Slash command bodies stay unchanged; the Bash prefix branches on the flag.
- [ ] Assertions per stage: state advanced correctly, expected artifacts exist, `events.jsonl` contains the expected event types in order, `audit.md` renders.
- [ ] Run the E2E in CI on every push to a feature branch. Fail loudly on any unexpected event or state.
- [ ] Add a second E2E that exercises the **bounce loop** (validate → followups → bounce → validate → followups → complete) and a third for **abandon** at a random non-terminal state.
- [ ] Document how to add a new E2E scenario in `agent-workbench-live/tests/README.md`.

## 2. Context Graph

## 3. Followup spawn (TODO §1f stretch, deferred)

The pass-3 Renovate work landed the `followups` stage but **deliberately did not implement** the `agent-workbench followup spawn` command. That command — create a new `draft` run pre-populated from a chosen mini-brief in a prior run's `follow-ups.md` — is the natural next step now that follow-ups are first-class.

- [ ] Add `agent-workbench followup spawn <run_id> <n>` (or `--title <substr>`). Reads `runs/<run_id>/stages/followups/follow-ups.md`, picks entry N (1-indexed) or the first entry whose title matches, derives a `raw-idea.md` from `motivation` + `suggested_scope`, runs the equivalent of `new-run` against the same repo as the source run.
- [ ] Decision: does the spawned run inherit the source run's `repo-path` automatically? Default yes; override via `--repo-path`.
- [ ] Slash command `/followup-spawn` — thin wrapper.
- [ ] Event: emit a `FollowupSpawned` event in the *source* run's events.jsonl noting which entry was picked + the new run_id (so spawn lineage is queryable).
- [ ] Test: spawn from a recorded entry → new run lands in `draft` with correct raw-idea.
