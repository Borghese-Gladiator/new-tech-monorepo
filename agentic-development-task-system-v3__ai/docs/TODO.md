# TODO

## 1. Each worktree owns its own run dir

### Why this is here

Today the workbench's `runs/<id>/` directories are created relative to the workbench checkout the CLI happens to be launched from (`Config.runs_path = self.root / self.paths.runs_dir`, `lib/config.py:82-83`; `root` resolves to whichever `bin/agent-workbench` was on `$PATH`, per `bin/agent-workbench:17-22`). Because the master checkout and every worktree both contain a copy of `agent-workbench-live/`, the same `runs_dir` resolves to different physical locations depending on CWD. Run artifacts have been landing in master's working tree even when the run's worktree is the one doing the work.

Observed today on `master`:

```
Untracked files:
  agent-workbench-live/runs/2026-05-24-fix-generated-lines-base-ref-head/
  agent-workbench-live/runs/2026-05-24-token-efficiency-pass-2/
```

Both runs have live worktrees under `~/GitHub/LOCAL_worktrees/...`. The `fix-generated-lines` worktree's `git status` is clean — its run dir is sitting in master instead. Once another branch is ready to merge, master is dirty and the merge is blocked or risky. This is the classic "root repo is doing two jobs (integration workspace + runtime artifact store)" failure mode.

The fix: **the run dir lives in the worktree that's executing the run.** Master only sees a `runs/<id>/` when it arrives there via the `complete → merge` (or `abandon → merge`) path that already exists (`5adca50 feat(complete): auto-merge worktree branch on human_review -> done`). Active runs are never in master's working tree.

### Design principles

- **One owner per run.** A run dir is created inside its worktree at `new-run` time and stays there for the whole live lifecycle. The worktree is the run's home.
- **Archival is the merge that already happens.** `complete` and `abandon` (today and going forward) merge the agent branch into master. The agent branch carries the run dir as committed history. After the merge, master has the full audit trail; the worktree gets removed.
- **`metadata.yaml` stays canonical.** Every path that today derives from `cfg.runs_path / run_id` instead reads from a `Run` value object that carries the run's absolute `run_dir`. No regex on path components, no CWD-relative resolution.
- **The board's view is a union, not a single glob.** Active runs = each live worktree's `runs/`. Archived runs = master's `runs/`. The board enumerates worktrees and merges. No new "registry" file; `git worktree list` is the source.
- **The pre-`start` problem is solved by creating the worktree earlier.** `draft` / `shaping` / `planning` / `ready` happen inside the worktree, not in master. `new-run` is what creates the worktree; `start` is what flips state to `building`. Abandoning a draft removes a real worktree — accepted tradeoff.

### Tasks — Part A: lifecycle and metadata plumbing

- [ ] **A1. Move worktree creation from `start` to `new-run`.** `lib/cli/cmd_new_run.py` currently writes the run dir under `cfg.runs_path` and stops. Update it to: (1) compute the target worktree path from `cfg.worktrees_path` + the slug, (2) `git worktree add` at the configured `base_ref`, (3) create the run dir inside the new worktree at `<worktree>/agent-workbench-live/runs/<run_id>/`, (4) write `metadata.yaml` with `target.worktree.path` populated immediately. `cmd_start.py` becomes a state-only transition (`ready → building`) with no `git worktree add`; existing branch-creation logic stays. Update the lifecycle docs (`docs/lifecycle.md`) to match.
- [ ] **A2. Add an explicit `run_dir` to the `Run` lookup.** Today there's no first-class `Run` object — call sites do `cfg.runs_path / run_id` ad hoc. Introduce a `lib/runs.py` (or extend `lib/metadata.py`) with a `find_run(cfg, run_id) -> Run` that returns a dataclass: `run_id`, `run_dir: pathlib.Path` (absolute), `worktree_path: pathlib.Path`, `status`, `metadata: dict`. Lookup walks: master's `cfg.runs_path` + every entry in `git -C <workbench-repo> worktree list --porcelain` joined with `agent-workbench-live/runs/`. First match wins; collision is a hard error (with both paths in the message).
- [ ] **A3. Threads `run_dir` through transitions, events, metadata writers.** `lib/transitions.py`, `lib/metadata.py`, `lib/events.py` currently derive paths from `cfg.runs_path / run_id`. Replace those derivations with the `Run.run_dir` field passed in from the caller. Audit every `cfg.runs_path` usage in `lib/`; each one becomes "find the run, use its `run_dir`" or "enumerate all runs across worktrees" depending on whether it's a single-run write or a multi-run read.
- [ ] **A4. `complete` commits the run dir on the agent branch before merging.** `lib/cli/cmd_complete.py` (the auto-merge from `5adca50`) currently merges the agent branch as-is. Add a pre-merge step: inside the worktree, `git add agent-workbench-live/runs/<run_id>/` and commit with a deterministic message (`runs: <run_id> (complete)`) if anything in the run dir is uncommitted. The merge then pulls the run dir onto master as part of the same `--no-ff` merge that delivers the feature. Failure mode: if the worktree's working tree has unrelated uncommitted changes, the existing dirty-worktree refusal handles it.
- [ ] **A5. `abandon` mirrors `complete`'s archival path, into a separate subdir.** `lib/cli/cmd_abandon.py` today removes the worktree without preserving the run dir on master. Change it to: (1) commit the run dir on the agent branch (same pre-step as A4), (2) merge the agent branch into master at a different destination — write a `runs/abandoned/<run_id>/` subtree on master via a `git read-tree` or a renamed-on-merge step, (3) remove the worktree and delete the branch. The merge commit message names it clearly (`abandon: <run_id>`). This preserves postmortem material without polluting `runs/` with live-looking artifacts.

### Tasks — Part B: board, metrics, doctor

- [ ] **B1. Board enumerates runs across master + all live worktrees.** `lib/board/source.py` currently reads from `cfg.runs_path`. Replace the single-glob enumeration with: master's `cfg.runs_path` (archived runs after merge) + every workbench worktree's `runs/` directory. De-duplicate by `run_id`; on collision (a run dir exists in both a worktree and master with the same id), prefer the worktree's copy (it's the live one) and print a warning to stderr. `lib/cli/cmd_board.py` and `lib/board/app.py` pass through unchanged once the source is fixed.
- [ ] **B2. Metrics rollup follows the same enumeration.** `lib/metrics/rollup.py:57-63` does `cfg.runs_path.glob("*")`. Switch to the same union-of-worktrees enumeration from B1. Extract the enumeration into a single helper in `lib/runs.py` so the board and rollup share one implementation.
- [ ] **B3. `doctor` checks for orphan run dirs.** `lib/cli/cmd_doctor.py` should detect the failure mode this section fixes: any `runs/<id>/` directory in master's working tree whose `metadata.yaml` shows a status other than `done` or `abandoned` is an orphan from the old behavior. Print as a warning with the suggested fix (move into the named worktree's `runs/`, or commit + merge if the run is already complete).

### Tasks — Part C: tests + migration

- [ ] **C1. E2E fixture update.** The existing `happy/` and `bounce_pass2/` fixtures in `tests/test_e2e.py` assume run dirs live in the workbench root. Update them to assert run dirs live inside the worktree. Add a new fixture that drives two parallel runs simultaneously and asserts each lives in its own worktree, master's working tree stays clean throughout, and both end up archived in master after `complete`.
- [ ] **C2. Unit test for `find_run` enumeration.** Synthetic tmp workbench with master + two worktrees + one run in each. Assert `find_run` resolves by `run_id` correctly; assert collision raises with both paths in the message; assert removing a worktree makes its runs invisible until the worktree is re-added.
- [ ] **C3. Backfill / migration for the two current orphans.** The two untracked run dirs in master today (`2026-05-24-fix-generated-lines-base-ref-head/` and `2026-05-24-token-efficiency-pass-2/`) need to be moved into their respective worktrees as part of landing this section. Write the migration as a one-shot script in `tools/migrate_orphan_runs.py` that: (1) reads each run dir's `metadata.yaml` to find its `target.worktree.path`, (2) `git mv` the dir into `<worktree>/agent-workbench-live/runs/<id>/` (since they're untracked, `mv` suffices), (3) leaves master's working tree clean. Run once, then delete the script.
- [ ] **C4. Documentation sweep.** `architecture.md` § "Why orchestration is centralized" implies all artifacts live in the workbench root. Update it to describe the new model: workbench root is the integration target; live runs live in worktrees; archival happens via the existing `complete`/`abandon` merge. `agent-workbench-live/AGENTS.md` § "Source of truth" already says `metadata.yaml` wins over directory names — extend it with the one-sentence rule that the run dir's physical location is "inside the worktree until `complete`/`abandon`, on master after."

### Acceptance

- `git status` on master is clean of `agent-workbench-live/runs/*` untracked entries after a fresh `new-run` for an unstarted run (the run dir lives in its worktree, not master).
- A run can advance through `draft → shaping → planning → ready → building → validating → human_review → done` with master's working tree staying clean the entire time.
- `agent-workbench complete <id>` produces a merge commit on master whose tree contains the run dir at `agent-workbench-live/runs/<id>/` with full artifacts (brief, plan, build summary, QA report, HUMAN_REVIEW.md, audit.md, events.jsonl).
- `agent-workbench abandon <id>` produces a merge commit on master whose tree contains the run dir at `agent-workbench-live/runs/abandoned/<id>/`, and the worktree + agent branch are gone.
- `agent-workbench board` shows live + archived runs from one invocation; the two are visibly distinguishable (e.g. a `(archived)` suffix or column).
- `agent-workbench metrics --all` rolls up across both live worktrees and archived runs without double-counting.
- `agent-workbench doctor` reports zero orphans after migration.
- Two parallel runs can land their feature branches into master without ever needing `git stash` on master.

### Non-goals

A registry file or central index of runs (the union-of-worktrees enumeration is the index — `git worktree list` is already authoritative); supporting runs outside a worktree (the lifecycle now requires one from `new-run` onward); changing how `target.repo.path` works (this section is about *workbench* run-dir location, not *product* repo location); migrating already-merged historical runs (they're fine where they are on master); preventing the human from manually editing run files inside a worktree (they can — `metadata.yaml` editing is still gated by the transition engine, everything else is open).

### Origin

Surfaced 2026-05-24 while reviewing master's working tree state during a multi-worktree session. Two run dirs were sitting uncommitted on master while their owning worktrees were clean — the same root-as-runtime-artifact-store conflict described in the "best approach for run files" external doc. The doc's recommended fix (externalize runs entirely) was rejected because runs are first-class committed deliverables in this workbench; the narrower fix is to make the worktree their home for the live portion of the lifecycle and let the existing auto-merge be the archival path.

---

## 2. Structured human_review handoff output

Discovered 2026-05-24 while reviewing the CLI's human_review landing output. The `STOP.` banner (shipped in `9eda554`, `lib/cli/_stop_banner.py`) lands the agent's attention, but the *content* the banner carries is currently inconsistent across call sites: `cmd_followups.py` prints a terse "Next moves" command list with no summary; `cmd_validate.py` (the dogfood example) prints a hand-typed multi-paragraph block with commit SHA, test counts, and per-artifact links inline. Same lifecycle event, two very different shapes. The agent — and the human reading the agent's tool output — has to re-derive what's load-bearing each time. This task pins a single structured shape.

### Design principles

- **Banner is a pointer + minimum decision info; HUMAN_REVIEW.md is canonical.** The banner exists so the human can decide *whether to open HUMAN_REVIEW.md* (or which of `/complete`/`/bounce`/`/abandon` to type without opening anything). Anything that belongs in HUMAN_REVIEW.md (branch, commit SHA, full file-by-file diff, test result counts, per-artifact links, known issues, run timeline) does NOT belong in the banner. The renderer in `lib/human_review.py` already produces all of that — the banner must not duplicate it.
- **Worktree paths are not memorizable.** Each run lives in a worktree under `~/GitHub/LOCAL_worktrees/...` with a date-and-slug name the human did not pick. The banner MUST print the absolute path to HUMAN_REVIEW.md so the human can open it without re-deriving the worktree directory.
- **Decision text, not commands.** The "next moves" lines are reminders, not copy-pasteable CLI invocations. The human types the decision in a Claude Code session, not at a shell. Drop the `agent-workbench complete <run-id> --accepted-by ...` form; keep one-line descriptions of what each decision *does*.
- **One source of truth for the banner content shape.** Same helper drives every agent-stopping transition's banner content (`lib/cli/_stop_banner.py` pins the *frame*; this task pins the *body* for `human_review` landings specifically). Wording stays in sync across `cmd_validate.py` and `cmd_followups.py`.
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
| Diffstat | `git diff --shortstat <base_ref_sha>..HEAD` inside the worktree, formatted into the single line shown. (Uses the `metadata.target.repo.base_ref_sha` field added in `303bd40`.) |
| Next moves | Static — one line per terminal action, with text descriptions, not full CLI commands. |

### Tasks

- [ ] **Extend `lib/cli/_stop_banner.py` with a `human_review` body builder.** That helper currently maps landing state → static next-moves text. Add a sibling function `_build_human_review_body(cfg, run_id) -> str` that reads HUMAN_REVIEW.md, extracts the first ≤3 `## Summary of changes` bullets, builds the testing line from the QA report's outcome (`tests_passed: true` + `known_issues_count: 0` → "Unit tests passed; no known issues."; `false` → "Unit tests failed (see HUMAN_REVIEW.md)."; manual/dogfood mentions get a second sentence), and runs `git diff --shortstat` inside the worktree. `print_stop_banner(landing_state="human_review", run_id=...)` calls this builder; other landing states keep the current static text.
- [ ] **Truncation discipline.** The summary-of-changes extractor caps at 3 bullets. If HUMAN_REVIEW.md has more, append the literal line `  …(<N> more in HUMAN_REVIEW.md)`. Each bullet is single-line truncated at ~100 columns with `…` if longer. The testing line is capped at 2 sentences; if the renderer would produce a third, it's dropped.
- [ ] **Decision text replaces command text.** Rewrite the existing `Next moves` block — both in `cmd_followups.py`'s current output and in `cmd_validate.py`'s ad-hoc block — to the three-line form shown above (`/complete <run-id>`, `/bounce <run-id>`, `/abandon <run-id>`, each with a short description). Remove the `agent-workbench complete ... --accepted-by ...` shell form entirely.
- [ ] **Diffstat fallback.** If `base_ref_sha` is missing (pre-`303bd40` runs), fall back to `git diff --shortstat <base_ref>..HEAD`. If that's empty (e.g. `HEAD..HEAD`), print `Diffstat: unavailable (base_ref unresolved).` rather than a misleading "0 files changed."
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

PR links (no support yet — out of scope until the workbench grows GitHub integration). Loud-card / color escape sequences (banner stays ASCII-only, per `_stop_banner.py`). A banner shape for `done` / `abandoned` landings (those are terminals — the existing static text in `_stop_banner.py` is enough). A banner shape for `ready` (planning landing — different decision set, different shape, separate task). Moving any field currently in HUMAN_REVIEW.md into the banner. Auto-opening the file in `$EDITOR` on landing (the human chooses when to read).

### Origin

Surfaced 2026-05-24 during a session reviewing the CLI's `human_review` landing output across the stop-banner dogfood run (`9eda554`) and the prior fix-generated-lines run. The two runs printed structurally different "what to review / what to decide" content for the same lifecycle event. The user pinned the rule: banner = pointer + minimum decision info; HUMAN_REVIEW.md = canonical detail.
