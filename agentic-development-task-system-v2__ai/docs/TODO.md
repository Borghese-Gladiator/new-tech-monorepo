# TODO

Next round of work after V1. Each section captures one idea — what it is, why we want it, and the concrete pieces to build.

**Completed work, summarised at the top so this file shrinks over time:**

- ✅ Renovate task workflow (originally §1; 1a–1g across four commits `d1d8b44`, `d5ee45e`, `90a3daf`, `827a06a`).
- ✅ Better worktree name (originally §2 after renumbering; merged into `202605_agent_workbench_v2` from `agent/better-worktree-name-template`).
- ✅ Numbered stage directories (originally §1 after this renumbering; `stages/1_draft/`, `2_shaping/`, …). Same dogfood pass cleared four follow-ups: scope_check path-prefix matching, `extract_run_date` unit tests, `show` rendering the `build:` block, multi-line ASM/DR body parsing.
- ⚠️ Task board v0 (originally §1, commit `0fe9214`) — shipped a simple `agent-workbench board` / `/board` that prints a static text Kanban grouped by lifecycle state. Superseded by the live Textual TUI below (`f10b6d8`); the v0 contract survives as the `--static` fallback path.
- ✅ Live task board — Textual TUI (originally §1 after renumbering, commit `f10b6d8`). `agent-workbench board` launches a full-screen Textual app over `runs/` with a watchdog file-watcher + 1Hz fallback timer; cards re-render on every `metadata.yaml` / `events.jsonl` change. Status-aware card bodies, loud-card highlighting, `--static` / `--compact` / `--all` / `--status` knobs. `textual` + `watchdog` shipped as a `[board]` optional-deps group (`requirements-board.txt`) — core CLI stays stdlib-only.
- ✅ Live board card attributes (originally §2 after renumbering, commits `549c9aa` + `445f3cd` + `52926b5`). Eleven on-disk fields that the anemic v1 card body never surfaced now render status-aware: lifecycle state badge, scope kind, idle/`● live` signal, AC coverage (parsed from build.md), git diff shortstat (cached on `(run_id, updated_at)`), avg iteration time, bounce origin, followup category breakdown, repo-path tail, terminal-card `accepted_by`/`abandoned_reason`, worktree-existence flag, tests-recorded age. Dogfood (`445f3cd`, run `2026-05-22-s2-attrs`) drove a fresh `repair`-scope run through every column and surfaced one renderer bug — the static path's `human_review` branch missed the followups-category breakdown — fixed inline and locked in by a regression test (`52926b5`).

Order reflects priority: board UX polish, E2E, context graph, followup spawn.

---

## 1. Live board — UX polish on the card layout

The Shogi dogfood (and the §2 work that surfaced the missing fields) made the second class of problems clear: the card is a wall of dim grey text with no visual hierarchy. A UX engineer would not let this through review. The data is there; the rendering needs structure.

- [ ] **Card bands, separated by horizontal rules.** Today the card is a single Rich `Text` blob using `dim` for everything below the title. Restructure into four bands joined by `─` rules:
  1. **Title band** — slug + state badge.
  2. **Meta band** — age in stage · total age · repo · branch.
  3. **Body band** — status-specific progress (build bar, tests/rev/qa marks, follow-up counts, etc.).
  4. **Events band** — last 3 events with column-aligned timestamps.
  5. **Files band** — labelled, abbreviated paths (see the path-formatting bullet below).

  Each band answers exactly one question. The eye stops looking once it has the answer.
- [ ] **Trim the title.** Run IDs are `YYYY-MM-DD-<slug>`. Six identical date characters lead every card. Render the slug bright + the date dim, or move the date into the meta band entirely so the title is just the slug.
- [ ] **Column-aligned event timestamps.** Today each event line reads `ArtifactWritten · 4s ago`. Change to `[mm:ss ago] EventType detail` with the timestamp left-aligned in a fixed-width column. Gives the eye an anchor and makes ordering legible at a glance.
- [ ] **Graded loudness.** Today any of {stale-review, max-iter, failing-tests, known-issues, recent-error} flips the same red border + same `!` marker. Split into two levels:
  - **Warning** (yellow border, `⚠` marker): `known_issues > 0`, recent error, stale-but-not-blocking.
  - **Blocking** (red border, `✕` marker): failing tests, builder gave up (`exit_reason == max_iterations`), stale-stuck `human_review`.
  Surface the *reason* in one body line (`⚠ tests failing` / `✕ builder gave up 5/5`) so loudness is self-explaining.
- [ ] **Column subtitle.** Under `followups (1)` add a one-line "brainstorm next bites"; under `validating` add "review + QA in flight"; etc. Helps a new reader without a glossary. Pull strings from a per-state constant in `lib/board/source.py`.
- [ ] **Audit paths: label, abbreviate, separate.** Currently the run-dir + worktree paths render as two long dim-italic strings at the end of the card with no labels — on a 40-char card, a 130-char absolute path wraps into four indistinguishable lines. Fix:
  - Label each path (`run` / `wt`).
  - Replace `$HOME` with `~`; replace the workbench root with `…`. Reduces a typical line from ~140 chars to ~45.
  - Place them in their own band separated by a horizontal rule.
  - Layout target:
    ```
    ─── files ──────────────────────────────
     run  ~/…/runs/2026-05-22-shogi-core
     wt   ~/…/worktrees/repo/20260522__shogi-core
    ```
- [ ] **`--verbose` / `--no-paths` knob.** Most board sessions don't need absolute paths visible — the reviewer is watching state, not `cd`-ing around. Default the files band to *off* and add `--verbose` to opt in. (Alternative if simpler: drop the files band entirely from the default card and keep it in the `agent-workbench show <id>` text output where it already lives.)
- [ ] **Don't let `dim` carry semantic weight.** Today the only contrast on the card body is "title bold / everything else dim". Use the default body style for primary content (events, body band) and reserve `dim` for actually-secondary text (meta band, files band). One axis of contrast doing one job.
- [ ] Snapshot tests for the layout don't make sense (visual), but the renderer should have small unit tests that assert per-band content selection: e.g. given a snapshot with `followups_entry_count=5`, the body band string contains `5 follow-ups` and the events band starts with the youngest event's age.

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

## 3. Context Graph

## 4. Followup spawn (TODO §1f stretch, deferred)

The pass-3 Renovate work landed the `followups` stage but **deliberately did not implement** the `agent-workbench followup spawn` command. That command — create a new `draft` run pre-populated from a chosen mini-brief in a prior run's `follow-ups.md` — is the natural next step now that follow-ups are first-class.

- [ ] Add `agent-workbench followup spawn <run_id> <n>` (or `--title <substr>`). Reads `runs/<run_id>/stages/followups/follow-ups.md`, picks entry N (1-indexed) or the first entry whose title matches, derives a `raw-idea.md` from `motivation` + `suggested_scope`, runs the equivalent of `new-run` against the same repo as the source run.
- [ ] Decision: does the spawned run inherit the source run's `repo-path` automatically? Default yes; override via `--repo-path`.
- [ ] Slash command `/followup-spawn` — thin wrapper.
- [ ] Event: emit a `FollowupSpawned` event in the *source* run's events.jsonl noting which entry was picked + the new run_id (so spawn lineage is queryable).
- [ ] Test: spawn from a recorded entry → new run lands in `draft` with correct raw-idea.
