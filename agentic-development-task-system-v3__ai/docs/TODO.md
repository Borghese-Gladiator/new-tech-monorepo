# TODO

## 1. Lifecycle papercuts: `.lock` in `.gitignore` and the `ready` banner

Two unrelated one-shot fixes grouped because they're both tiny, both touch the agent-stopping handoff path, and both have a clear single-line shape. Worth landing together to avoid a near-empty section per item.

### 1a. `runs/*/.lock` not gitignored — every `/complete` falls back to `--no-merge`

`locks.acquire(cfg, run_id)` creates `runs/<id>/.lock` inside the run directory before `repos.merge_no_ff` runs `worktree_dirty_files(repo_path)`. The run dir is tracked in the parent repo, so the lock file appears in `git status --porcelain` and the merge refuses with `refusing to merge: <repo> has uncommitted changes: ['runs/<id>/.lock']`. Workaround so far has been `complete --no-merge` + manual `git merge --no-ff` + `tools/backfill_completion_refs.py`. Hit on at least three runs (stop-banner, token-efficiency-pass-2, structured-human-review-handoff).

Root `.gitignore` is currently just `tmp/`; the entry has to be added.

- [ ] Add `agentic-development-task-system-v3__ai/agent-workbench-live/runs/*/.lock` to root `.gitignore` (also add the v2 sibling path if v2 still produces lock files).
- [ ] Verify by running `/complete` on a real run after the entry lands — the dirty-files check should pass without `--no-merge`.
- [ ] Update `tools/backfill_completion_refs.py`'s docstring/comments to reference this fix and note that the backfill is no longer needed for new runs.

### 1b. `ready` banner still uses shell-form

`_SPECS["ready"]` in `lib/cli/_stop_banner.py` prints `agent-workbench start <id>` as the next move. `human_review` was migrated to slash-form (`/complete`, `/bounce`, `/abandon`) in the structured-handoff run (`a698f62`); `ready` was explicitly out-of-scope there. The inconsistency is now visible to anyone watching two banners in a row.

- [ ] Change `_SPECS["ready"]` to render `/start <id>` with a one-line description (e.g. "approve the plan and create the worktree").
- [ ] Re-baseline `tests/snapshots/stop_banner_ready.expected.txt`.
- [ ] No new structured-body builder required — `ready` has one decision; the five-section shape isn't justified.

### Acceptance

- `/complete <id>` on a run that committed its run dir produces a successful `git merge --no-ff` without needing `--no-merge`.
- `_stop_banner.py` contains no `agent-workbench start` literal; the `ready` banner snapshot reflects the slash-form.

---

## 2. `base_ref_sha` plumbing — three remaining consumers + audit trail + backfill

`303bd40` added `target.repo.base_ref_sha` to `metadata.yaml` and threaded the prefer-SHA / lazy-resolve / fallback pattern into `lib/metrics/lines.py`. Three other consumers still take a symbolic `base_ref` and produce wrong or empty output when the recorded value is `"HEAD"`; a backfill tool for pre-fix runs is also unwritten, and the audit log doesn't record the resolved SHA at all.

### 2a. `lib/validate_context.py` — empty diff against worktree branch HEAD

`validate_context.build` and `build_blast_radius` take `base_ref: str` and shell out `git diff <base_ref>...HEAD` literally. With `base_ref="HEAD"`, that resolves to the worktree HEAD vs. itself — the diff is empty even when the worktree has real commits. Downstream: the reviewer's blast-radius narrative is fed an empty file list and validate-context.md's "Files changed" block reads `(no files changed yet)`.

- [ ] Add a `base_ref_sha: str | None = None` kwarg to `validate_context.build` and `build_blast_radius`. Prefer the SHA when present; fall back to symbolic `base_ref` lazy-resolve when missing. Mirror `lib/metrics/lines.py:_effective_ref`.
- [ ] Thread the SHA through `cmd_validate.py:_write_validate_context_artifacts` (read `meta["target"]["repo"]["base_ref_sha"]` alongside `base_ref`).
- [ ] Confirm the diff target is the worktree path (it already is) and that the SHA was originally captured against the source repo (it was).
- [ ] Unit test against a synthetic two-commit worktree — would fail today, pass after.

### 2b. `lib/board/source.py:_git_shortstat` and `lib/doc_claims.py:_verify`

Both still take symbolic `base_ref`. Neither is *broken* in the same observable way as 2a (the triple-dot diff produces *a* number when `base_ref="HEAD"`), but the type signature has drifted: `lines.py` knows about `base_ref_sha`, these two don't. Pure type-symmetry / consistency play.

- [ ] Add `base_ref_sha` kwarg to `_git_shortstat` and `verify`; lazy-fallback chain identical to `lines.py:_effective_ref`.
- [ ] Update call sites (`board/source.py:566` and the `doc_claims.verify` call in `cmd_validate.py`).
- [ ] Parallel unit tests in `tests/test_board_snapshot.py` and `tests/test_doc_claims.py`.

### 2c. Backfill tool for pre-`303bd40` runs

`tools/backfill_completion_refs.py` exists for merge SHAs; no equivalent for `base_ref_sha`. Runs like `2026-05-22-token-efficiency-tracking` whose `base_ref: "HEAD"` was captured before this run still report `generated_lines: 0` even after a `metrics --rebuild` (the lazy resolver inside the worktree can't recover the original fork point once HEAD has advanced).

- [ ] Write `tools/backfill_base_ref_sha.py`. Walk `runs/*/metadata.yaml`. For each entry with symbolic `target.repo.base_ref` and missing `target.repo.base_ref_sha`, compute the fork point — preferred: `git merge-base <target.worktree.branch_name> <agent-workbench.yaml-default-base-ref>`; fall back to `git rev-list --max-parents=0 <branch>` when merge-base fails. Write via `metadata.update`. Idempotent. `--dry-run` flag.
- [ ] After the script lands, run it once on this repo and verify `agent-workbench metrics --rebuild` against the pass-1 dogfood run reports non-zero `generated_lines` (TODO §3 acceptance from the prior fix-generated-lines TODO).

### 2d. `BaseRefResolved` event

The resolved SHA only lives in `metadata.yaml`. The audit trail (`events.jsonl`) records the transition with `base_ref: "HEAD"` symbolic and nothing else. Two consequences: (1) line counts can't be re-derived from the audit log alone, (2) drift between `metadata.yaml` and the original resolved SHA is undetectable.

- [ ] Add `BaseRefResolved` to `schemas/events.jsonl` with payload `{symbolic_ref, sha, source_repo_path}`.
- [ ] Emit from `cmd_start.py` immediately after `repos.resolve_ref_to_sha` succeeds, before the `building` transition.
- [ ] Surface in `lib/audit.py`'s `audit.md` render.
- [ ] Forward-only. Don't synthesize events for old runs — pair with the backfill tool (2c), which writes metadata only.

### Acceptance

- `validate-context.md` "Files changed" block lists real worktree-branch commits for any run whose metadata carries `base_ref_sha`.
- `agent-workbench metrics --rebuild` against `2026-05-22-token-efficiency-tracking` reports a non-zero `generated_lines` after the backfill script runs.
- `events.jsonl` for new runs contains a `BaseRefResolved` event between the `planning → ready` and `ready → building` transitions.
- Grep for `base_ref:` in `lib/board/source.py` + `lib/doc_claims.py` finds calls that also accept `base_ref_sha`.

---

## 3. Schema-level validation for `metadata.yaml` on load

`lib/metadata.py:_validate` enforces top-level keys + the status enum only. `schemas/run-metadata.yaml` is descriptive — `metadata.load()` doesn't read it. Typos like `bse_ref` instead of `base_ref` load silently, surface later as missing-field crashes or wrong-data renders. As fields proliferate (`base_ref_sha`, `target.worktree.branch_name`, the `build:` block, the new `completion:` shape), the surface area for silent drift grows.

- [ ] Add a lightweight YAML-schema validator (or hand-roll typed accessors that raise on missing-or-mistyped) that walks `target.repo`, `target.worktree`, `validation`, `completion`, `build` and enforces field types + enum values on load.
- [ ] Surface mismatches as warnings by default; error behind a strict mode toggled in `agent-workbench.yaml`'s policies block.
- [ ] Keep `artifacts` and `scope` un-validated for this pass — they're free-form by design.
- [ ] Update `schemas/run-metadata.yaml` to be load-bearing rather than descriptive; document the field-type contract in `lib/metadata.py`'s module docstring.

### Acceptance

- A `metadata.yaml` with a typo'd top-level key under `target.repo` produces a warning at load time and an error under strict mode.
- Existing `runs/` directories load without warnings (no false positives on real data).
- `tests/test_metadata.py` covers at least: missing required field, mistyped scalar, enum violation, additive backward compat (unknown extra key tolerated under default mode).

---

## 4. Test-coverage gaps

Six gaps that have shown up twice or more across follow-ups since 2026-05-24. Grouped because they all share the same shape: a code path that's verified by code-reading or by tmp-dir structural assertions, but doesn't have a runtime drive-and-assert.

- [ ] **Full self-modifying lifecycle E2E.** `tests/test_self_modifying.py` covers `new-run` only (`test_new_run_creates_worktree_and_clean_master`). Add a test that drives `shape → plan → start → validate → complete` end-to-end on a synthetic self-modifying workbench; assert master's `git status --porcelain` is clean of `runs/` entries at every step and that the final merge commit contains the run dir at the worktree-side path. Reuse `_make_self_modifying_workbench` from the existing class.
- [ ] **Flat-layout E2E fixture.** `cmd_validate.py`'s flat path (`validating → human_review` directly) is the only one of the five banner sites without runtime coverage. Add `tests/fixtures/flat_happy/` (or similar) and a test method mirroring `test_happy_path` minus the followups stage. Asserts `STOP.` appears after `validate` and not after `validate --init`.
- [ ] **No-banner-on-abort runtime test for `cmd_complete`.** The existing `TestE2ECompleteMerge::test_merge_conflict_aborts_and_stays_in_human_review` checks status + events but does not assert `STOP.` is absent from stdout. Add the assertion (or a sibling test) so a future refactor that moves the banner above the failure paths fails loudly.
- [ ] **Direct unit tests for `lib/repos.py:stage_and_commit_run_dir` and `archive_tree_to_path`.** Only exercised via `cmd_complete` / `cmd_abandon` integration today. The `--strip-components` count in `archive_tree_to_path` depends on the source path's segment count and would benefit from a focused fixture (2-segment vs. 4-segment source paths).
- [ ] **Snapshot test for the full `human_review` stop banner.** Today the structured body is checked by `TestFullBanner` structural assertions + E2E `assertIn` substring checks; wording drift in the body (e.g. "auto-merges worktree branch into parent" → "merges into parent") would pass. Reuse the `_normalize`-style helper from `tests/test_human_review.py` (collapse `<TMP>`, `<TEST_REPO>`, `<HH:MM:SS>`, `<RUN_ROOT>`) and add two fixture-driven snapshots — one for the happy path, one for bounce-pass2 — under `tests/snapshots/stop_banner_human_review_{happy,bounce_pass2}.expected.txt`.
- [ ] **`_write_validate_context_artifacts` error-path coverage.** `cmd_validate.py:82-84` wraps the whole generator in `try: ... except Exception: pass`. The convenience-artifacts-must-not-break-the-transition intent is right, but the catch silences any bug in the generator. Add: (a) one test that monkey-patches `validate_context.build` to raise and asserts the transition still succeeds AND that the file is NOT written (proving the catch fired), (b) one test that constructs an unparseable `build.md` and asserts the generator produces a sentinel-fallback file rather than crashing. Optional: log the swallowed exception to `events.jsonl`.

### Acceptance

- All six gaps closed; suite count rises by the corresponding number of cases (rough estimate: +10 to +15 tests).
- Each new test would fail under today's behavior if the relevant code were reverted (verify by spot-check).

---

## 5. Board freshness across worktrees after the per-worktree run-dir landing

### Why this is here

The prior section moved live run dirs into their worktrees (`<worktree>/agent-workbench-live/runs/<id>/`), but the board's freshness infrastructure was scoped to master's `cfg.runs_path` only. Two coupled gaps remain, both surfaced 2026-05-25 while watching the board during this run's own `complete`:

**Gap 1 — watchdog observer covers master only.** `lib/board/app.py:561-573` schedules a single `watchdog.observers.Observer` on `cfg.runs_path` (master). Live writes inside worktrees (every `shape`/`plan`/`validate` artifact for any self-modifying run) fire no watchdog events. The 1Hz fallback timer (`self.set_interval(1.0, self._refresh)`) catches them eventually with up to ~1s lag, but instant refresh is lost.

**Gap 2 — `_list_workbench_worktrees` cache has no TTL.** `lib/runs.py:_WORKTREE_CACHE` is a process-lifetime dict keyed on workbench root path. First call populates it from `git worktree list --porcelain`; every subsequent call in the same process returns the cached tuple. For short-lived CLI commands this is fine (the process exits in milliseconds). For the long-running board, it means worktrees created mid-session are invisible until the board restarts — even with a 1Hz `iter_all_runs` rescan.

Observed concretely on 2026-05-25 while completing this run: the board showed the run stuck in `human_review` until manual restart. Two contributing causes — the board process predated the post-A1 `iter_all_runs` codepath (genuine version skew, not just lag), AND the cache would have masked any new worktree creation thereafter.

### Design principles

- **Optimize the long-running case differently from the one-shot case.** The board ticks for hours. CLI commands exit in <1s. The same cache that's correct for one is wrong for the other. Don't unify them; split.
- **`git worktree list` is not free.** Measured on the workbench's own repo with 3 worktrees: ~16ms median, ~19ms p90 per call. Scales linearly with worktree count. Calling it raw at 1Hz costs ~1.6% of one CPU continuously today; with 20 worktrees it'd be 5–8%. Don't pretend it's invisible.
- **Watchdog is the right tool for change notification.** The 1Hz fallback is a safety net, not the primary mechanism. Recursive `Observer.schedule` on every worktree's `runs/` dir is the canonical fix; the 1Hz tick should only be needed for "new worktree appeared since the last observer scheduled".
- **Don't redesign the source layer.** `RunSnapshot`, `iter_all_runs`, the severity model, the renderers — all post-A1 correct. The bug is narrow: filesystem-event coverage in `AgentBoardApp.on_mount`, plus the cache TTL.

### Tasks

- [ ] **Investigate the actual user-visible symptom space.** Before picking a fix, characterize what's slow and what's wrong:
  - How often does someone start a new worktree mid-board-session? (Affects whether dynamic re-scheduling is worth the complexity.)
  - How many worktrees do real users have at once? (Affects whether `git worktree list` cost is meaningful.)
  - Does the 1Hz fallback actually deliver perceived freshness for everything except the watchdog gap? (May reveal other latency sources.)
  - Is there a less obvious fix — e.g. having the CLI commands send a signal/file-touch the board listens for, instead of filesystem-event polling?
- [ ] **Decide on the watchdog strategy.** Three options on the table from the 2026-05-25 conversation; pick one (or a combination) based on the investigation:
  - **Option 1 — multi-root watchdog at startup.** In `AgentBoardApp.on_mount`, after the initial `obs.schedule(_Handler(self), cfg.runs_path, recursive=True)`, walk `runs.iter_all_runs(cfg)` once and call `obs.schedule(...)` for each unique worktree-side `runs/` directory. ~10 lines. Doesn't cover worktrees created mid-session.
  - **Option 2 — periodic re-scan of the worktree list.** Add a second `set_interval` (e.g. 30s) that diffs the current watcher set against `git worktree list` and adds observers for new worktrees. ~30 lines plus observer bookkeeping. Covers the mid-session case at the cost of complexity.
  - **Option 3 — watch the parent `cfg.worktrees_path` recursively.** One `obs.schedule(_Handler, cfg.worktrees_path, recursive=True)` covers every existing and future worktree. ~5 lines. Trade-off: noisy event stream (every product-code edit in every worktree fires a handler); the existing `_Handler` filter handles it cheaply but it's still busier.
- [ ] **Decide on the cache strategy.** The current process-lifetime cache is the right shape for short-lived CLI commands but wrong for the board. Options:
  - **Short TTL** (e.g. 2s): `_WORKTREE_CACHE: dict[str, tuple[float, tuple[...]]]`; check `time.monotonic() - cached[0] < TTL` before reuse. CLI calls still cache for their full lifetime (process exits well before TTL); board ticks see new worktrees within TTL seconds. ~10 lines. Doesn't require the board to know it's special.
  - **Drop the cache for `iter_all_runs`**: keep it only on `find_run`'s hot path. Board pays full `git worktree list` cost every tick (~16ms on a small repo, possibly higher on large). CLI commands lose a tiny optimization. Simplest.
  - **Explicit invalidation hook**: expose `runs.invalidate_worktree_cache()`; the board's 1Hz refresh calls it; CLI commands don't. Most surgical, ugliest contract.
  - **Don't change it at all**: rely on option 1 above (multi-root watchdog) to cover the freshness gap without re-scanning. If the user creates a new worktree mid-session that's still invisible until restart, but maybe that's acceptable.
- [ ] **Implement + test.** Whichever combination wins, add coverage:
  - Unit test for the cache behavior (TTL expiry, or invalidation-hook contract).
  - Integration test that launches the board (or its `snapshot.build` driver) against a synthetic workbench, creates a new worktree mid-test, and asserts the new run appears within the expected window.
  - Performance smoke: measure `snapshot.build(cfg)` wall-clock at 1Hz with N=3, N=10, N=20 worktrees. Confirm it stays under a budget (e.g. 100ms per tick).
- [ ] **Document the contract.** Whichever cache shape wins, write the rule in `lib/runs.py`'s module docstring so the next person doesn't re-introduce the same bug.

### Acceptance

- Board started before a new worktree exists shows the new worktree's runs within a documented bound (e.g. ≤ 2s for the TTL approach; ≤ 30s for the periodic-rescan approach).
- `git worktree list` is not called more than necessary — investigation has measured the cost on a representative worktree count and the chosen strategy beats today's worst case.
- A self-modifying run transitioning through `validate` → `followups` → `human_review` shows the column changes on the live board with ≤ 1s lag (matching today's 1Hz floor) without manual restart.
- `complete`/`abandon` terminal transitions are visible on the board without manual restart, and the previously-visible `human_review` card disappears cleanly (no stale row).
- New tests exist that would fail under today's behavior and pass under the new one.
- `lib/runs.py`'s module docstring explains the cache contract.

### Non-goals

Re-architecting the board's renderer (`RunSnapshot`, `lib/board/source.py`, `lib/board/snapshot.py` are all correct); replacing watchdog with a different filesystem-event library; building a daemon or message bus between CLI commands and the board (out of scope unless investigation surfaces it as the right answer); supporting non-git worktree change detection (e.g. NFS); changing the 1Hz fallback frequency (it's the safety net, not the target).

### Origin

Surfaced 2026-05-25 in a session debugging why this run (`2026-05-25-each-worktree-owns-its-own-run-dir`) stayed at `human_review` on the live board well after `complete` had merged it. Investigation traced the symptom to two layered causes: the board process predated the post-A1 `iter_all_runs` codepath (one-time skew, fixed by restart), AND the worktree-list cache had no TTL (would re-occur for any new worktree created mid-session). The user pushed back on a too-quick "drop the cache" fix — `git worktree list` was measured at ~16ms median, ~19ms p90, ~1.6% of a CPU at 1Hz today — and asked for an explore-then-decide approach rather than jumping to one of the four cache strategies above. Follow-up `follow-ups.md` from that run also called out the watchdog-coverage gap as a separate item; this TODO consolidates both.
