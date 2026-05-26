# TODO

## 1. Generalize the `*-context.md` cross-stage contract

Today `validate-context.md` is the only stage-boundary curated entry point — it's written deterministically by `validate --init` from prior artifacts (brief, plan, build, qa) so the reviewer reads one file instead of four. The pattern works (it's load-bearing for cache discipline; see the pass-1 dogfood's 121.8M `cache_read` tokens) and should be generalized to every LLM-bearing stage. Each `--init` step writes a `<stage>-context.md` containing exactly what the next stage needs, filtered from prior artifacts, with anchors pointing back to the full versions when the agent wants to go deeper.

The leverage is twofold:

1. **Cache footprint.** File reads in the master session stick in the prefix forever. Today the builder typically reads `brief.md` + `plan.md` + occasional `decisions.md` lookups; the reviewer (without the curated context) would read all of those plus the QA report plus the build summary. Each is a permanent prefix cost. One curated file per stage collapses that into a single read.
2. **Subagent-readiness.** A self-contained `<stage>-context.md` is the natural input for an Agent-tool subagent — the master spawns the subagent with that one file as context, the subagent's reads don't pollute the master's prefix, the master gets back structured findings. This is the same pattern the existing `Explore` rule uses; the cross-stage contract makes it the default shape for every LLM-bearing stage. The pre-PR adversarial reviewer (§7 `publishing` stage) depends on this — `validate-context.md` is already shaped right, but `build-context.md` and `plan-context.md` would need to exist before the subagent pattern can extend to those stages.

### What each file contains

**`shape-context.md`** (written by `shape --init`)
- Original raw idea (verbatim from `raw-idea.md`)
- Answers from `answers.md` if present
- `brief.md` template skeleton inlined with one-line section descriptions
- The two shaping rules: no code reading, no questions

This one is thinnest — shaping has the least prior context to filter. The win is mostly inlining the template so the agent doesn't context-switch into `templates/`.

**`plan-context.md`** (written by `plan --init`)
- Full `brief.md` (small, load-bearing)
- Repo map: top-level dirs, detected languages, build/test commands from `agent-workbench.yaml` policies or inferred from the worktree
- `brief.md`'s "Files likely to change" lifted inline (the planner should validate or refute this)
- `plan.md` template skeleton with section descriptions
- Rules reminder: may read code, may not ask questions, record assumptions

**`build-context.md`** (written by `start` or on `building` entry — needs a decision on which)
- Brief's Acceptance criteria + Non-goals (the scope-creep anchors)
- Plan's Proposed changes + Files likely to change + Test plan + Definition of done
- Filtered Decisions & assumptions from `plan.md#decisions--assumptions`
- Worktree path, branch name, base ref SHA (already in metadata, surfaced inline for the agent)
- `build.md` template skeleton
- Rules reminder: stay bounded by brief, record deviations in `build.md`

Highest leverage of the five. Today the builder typically re-reads brief and plan back-to-back at the start of the session, then dives into the worktree. `build-context.md` collapses those two reads into one curated file.

**`validate-context.md`** — already exists. This is the design template.

**`followups-context.md`** (written by `followups --init`)
- Brief's Non-goals (frequent source of follow-up candidates)
- Plan's Risks section
- Review's Decision + findings
- QA's Known issues
- Build's Deviations from plan
- `follow-ups.md` schema (category enum, frontmatter rules)
- Rules reminder: read-only, 1–5 entries or `no_followups` sentinel

### Tasks

- [ ] Build `build-context.md` first — highest leverage, lowest risk. Mirror `validate-context.md`'s deterministic-Python shape. Decide whether it's written by `start` (at the `ready → building` boundary) or on first `/build` invocation; `start` is cleaner because the file is ready before the LLM session begins.
- [ ] Build `plan-context.md` next. Will require some new code: detecting repo languages and surfacing build/test commands from `agent-workbench.yaml` policies. Some of this overlap with `repo-map`-style work the planner does today; the goal is to make that deterministic and front-loaded.
- [ ] Build `followups-context.md`. Likely thin — most of what it needs is already in the staged artifacts; the deterministic builder is mostly a filter + headline rollup.
- [ ] Build `shape-context.md` last (or skip if the inlined-template gain doesn't justify the code).
- [ ] For each, update the corresponding `.claude/commands/*.md` so step 1 reads `<stage>-context.md` rather than the prior artifacts directly. Mirror the `validate.md` step 2 language: "Do NOT re-read X if `<stage>-context.md` already covers what you need."
- [ ] Document the contract in `docs/lifecycle.md` — add a `*-context.md` row to each stage's table, sibling to "Reads" and "Produces."
- [ ] Each new `<stage>-context.md` builder gets unit tests that mirror `tests/test_validate_context.py`'s shape — synthetic prior artifacts → assert the generated context has the expected sections + anchor links.

### Acceptance

- Every LLM-bearing stage (`shape`, `plan`, `build`, `validate`, `followups`) has a `<stage>-context.md` generated by `--init` before the agent reads anything.
- A spot-check of three runs after the change shows the master session's prefix during each stage growing primarily from the curated file plus the worktree code the agent actively edits — not from re-reads of prior artifacts.

### Non-goals

Changing the artifact contents themselves (brief/plan/build/review keep their current sections); merging stages or changing the lifecycle; replacing template-driven artifact authoring with anything generative; building a `repo-map.md` artifact separate from `plan-context.md`'s repo-map section (keep it inline for now).

### Origin

Surfaced 2026-05-25 in a design conversation comparing agent-workbench to a proposed planner/implementer/reviewer/PR-writer system. The proposed system's "shared durable context, not many independent workers" framing matched what `validate-context.md` already does — but agent-workbench only built that pattern for the validate boundary. Generalizing is straightforward and the cache-discipline payoff is concrete (the proposal had no analog of this; agent-workbench's existing `validate-context.md` is strictly stronger and worth replicating across stages).

---

## 2. Lifecycle papercuts: `.lock` in `.gitignore` and the `ready` banner

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

## 3. `base_ref_sha` plumbing — three remaining consumers + audit trail + backfill ✅ shipped 2026-05-26 (run `2026-05-25-base-ref-sha-plumbing-across-remaining-con`)

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

## 4. Schema-level validation for `metadata.yaml` on load

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

## 5. Test-coverage gaps

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

## 6. Board freshness across worktrees after the per-worktree run-dir landing

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

---

## 7. Team-review delivery mode: GitHub PR creation lifecycle

Today the workbench is built for personal-repo, single-author work. `done` means "human accepted + locally merged to parent branch" — `cmd_complete` checks out the parent and runs `git merge --no-ff` directly. That model collapses two things that are separate in a team workflow: author sign-off and team sign-off. For team work the workbench needs to model the PR-review world as first-class lifecycle states, not a slash-command bolt-on after `done`.

The user-stated workflow:

> I give a Linear ticket so things are implemented → Human Review → approved means PR is created and run is marked as Done. If PR gets comments, it can get reopened somehow.

The key requirement: **the human must see and approve the PR draft before anything gets pushed**. PR descriptions are not a fire-and-forget concern — they're a structured artifact with its own review step. And `done` for team work cannot mean "auto-merged into master" — it should mean "PR exists, in team review, or merged."

### Design — Option A: per-run `delivery` mode with branched lifecycle

Add a per-run `target.delivery` field at `new-run` time:

```yaml
target:
  delivery: local-merge      # today's behavior, default for personal repos
  # or
  delivery: pull-request
  delivery_config:
    base_branch: main
    remote: origin
    auto_assign_reviewers: false
    update_strategy: append   # append | force_push
```

The state machine forks after `human_review` based on `delivery`:

```text
# delivery: local-merge (unchanged)
human_review -> done            (complete = local merge)
human_review -> building         (bounce)
human_review -> abandoned

# delivery: pull-request (new)
human_review     -> publishing         (author approves → draft PR)
publishing       -> in_pr_review       (after explicit /publish-pr — pushes + opens PR)
publishing       -> human_review       (bounce — draft rejected, doesn't push)
in_pr_review     -> changes_requested  (CI failure or reviewer comments)
in_pr_review     -> done               (PR merged)
in_pr_review     -> closed             (NEW terminal — PR closed without merge)
changes_requested -> building          (rebuild against curated change-request.md)
any non-terminal -> abandoned
```

### The new stages

**`publishing` — LLM-bearing, drafts the PR but does NOT push**

Reads `HUMAN_REVIEW.md`, `brief.md`, `review.md`, the diff, the Linear ticket if linked.
Writes `stages/7_publishing/pr-draft.md` (title + body) and `stages/7_publishing/pr-meta.yaml` (base branch, suggested reviewers, labels, linked tickets).
Also writes `stages/7_publishing/adversarial-review.md` — see sub-step below.
Stops with a STOP banner. The agent does not run `gh pr create`. The human reviews `pr-draft.md` + `adversarial-review.md`, edits the draft if needed, then runs `/publish-pr` to actually push the branch and create the PR — or bounces back to `human_review` if the draft or adversarial findings warrant it.

The draft is the artifact you said you need: "I want and need to see exactly what's going to get pushed." `pr-draft.md` is what gets pushed. Editing it before `/publish-pr` is the editing path; bouncing back to `human_review` is the redo path.

*Pre-PR adversarial review sub-step.* Before drafting the PR body, `publishing` dispatches an Agent-tool subagent (`general-purpose` or `Explore` with a tight allowlist) fed only `validate-context.md` + the diff. The subagent comes in cold — no builder chain-of-thought, no rationalizations from the implementing session — and returns a structured findings dict (Decision + list of `{section, severity, body}`). The master writes `adversarial-review.md` from the returned findings. This is distinct from `/validate`'s standard review (which is *not* adversarial and runs in the master session); the adversarial pass exists specifically because shipping to a team via PR is a higher bar than local human-review acceptance. The `/pr-review` skill's `adversarial` mode is the closest existing analog and can be reused or adapted. If findings include any `severity: blocker`, `publishing` refuses to write `pr-draft.md` and forces a bounce.

**`in_pr_review` — passive wait state**

No agent activity. The board shows `PR #1234 — N approvals, M comments, CI: passing/failing`.

State flips on external signal. Two trigger mechanisms (pick one or both):
- `agent-workbench pr-sync <run_id>` — polls `gh pr view --json state,reviews,comments,checksStatus` and emits the right events. Manual or cron.
- `gh` webhook → workbench-side listener — out of scope for V1, listed only so the architecture leaves room.

Events emitted by `pr-sync`:
- `PRApproved` — all required reviews pass + CI green → ready for human to merge
- `PRChangesRequested` — review left as changes-requested OR CI failed
- `PRMerged` → transitions to `done`
- `PRClosed` → transitions to `closed`
- `PRCommentsAdded` — non-blocking comments; no state change but events logged

Note: `PRApproved` does NOT auto-transition to `done`. The human runs `/complete` (or `/merge-pr`) to actually merge the PR. The workbench does not auto-merge team PRs even when CI + reviews are green — too many edge cases (squash vs merge vs rebase, branch protection rules, "wait for X to land first").

**`changes_requested` — bounce-with-curated-context**

Behaves like `human_review → building` bounce today (worktree preserved, prior stages archived under `archive/`), but with a critical difference: **`change-request.md` is pre-populated** from PR state by `pr-sync` before the bounce. Shape:

```markdown
# Change request — PR #1234 (round N)

## Reviewer threads
### thread 1 — src/exports/csv.py:147 (reviewer: alice)
> "This unconditionally loads all archived profiles into memory. Can we stream?"

### thread 2 — tests/test_exports.py:89 (reviewer: bob)
> "Missing explicit test for the false case."

## CI failures (if any)
- buildkite job xyz: pytest tests/test_exports.py::test_archived_filter — assertion failed (link)

## Untouched from prior build
- brief.md acceptance criteria (unchanged unless reviewer comments suggest replanning)
- plan.md (ditto)
```

The builder, on re-entering `building`, reads `change-request.md` first — it's the curated entry point (analog of `*-context.md` from TODO §1). The brief and plan are still available at their stage paths if the agent decides comments warrant replanning, but `change-request.md` is the default reading list.

A `changes_requested` bounce does **not** require re-running `/validate` from scratch the same way as today's `human_review → building` bounce does. Or maybe it does — open design question; see below.

**`closed` — new terminal state**

PR was closed without merge (declined, superseded, abandoned by team). Terminal. Distinct from `abandoned` because `abandoned` was the author's call; `closed` was the team's. Both preserve artifacts.

### What `/complete` does in `pull-request` mode

Today `cmd_complete` does `git merge --no-ff` into the parent branch locally. For `pull-request` runs, that's wrong — the merge happens on GitHub via the PR. Two options:

- **Option A1: `/complete` only valid in `in_pr_review` and only after `PRMerged` event landed.** It becomes a no-op transition (`in_pr_review → done`) that records `completion_ref: merge:<github-sha>` from the PR's `mergeCommitOid`. No local merge.
- **Option A2: `/complete` is renamed `/merge-pr` in `pull-request` mode and actually calls `gh pr merge`.** Workbench triggers the merge on GitHub. Higher control, higher blast radius (now the workbench is talking to remote APIs, which the architecture explicitly disclaims).

Lean A1. Keep the workbench's "we don't talk to remotes" stance intact. The human merges via the GitHub UI or `gh pr merge`; `/complete` just records the SHA and flips to `done`.

### Hard parts worth flagging

1. **Force-push vs. append on PR updates.** When the agent addresses comments and pushes again, force-push gives a clean diff but loses GitHub's comment-to-line anchoring; append keeps anchors but makes the PR a mess after 3 rounds. Configurable per-run via `delivery_config.update_strategy`. Default: `append` (safer, anchors preserved). Strong opinions differ team-to-team.
2. **CI failures vs. reviewer comments are different change types.** Both produce `changes_requested`, but CI failures are deterministic and the agent can act autonomously; reviewer comments often need judgment. Tag `change-request.md`'s top-level type (`ci_only`, `reviewer_only`, `mixed`) so a future automation can auto-bounce on CI-only failures without human intervention. V1: tag the field, don't act on it.
3. **Stale PR state on `/abandon`.** Abandoning a run with an open PR orphans the PR. `/abandon` for a `pull-request` run should default-prompt "Close PR #1234 too? [Y/n]" and call `gh pr close` if yes. Emit `PRClosed` event regardless of how the close happened.
4. **PR re-publishing after bounce from author-`human_review`.** If the author bounces from `human_review` (not from PR comments — there's no PR yet) and the worktree gets rebuilt, the next `publishing` stage drafts a fresh PR. If there's a *prior* PR draft from a previous loop, the `publishing` agent should diff its new draft against the prior one and surface the delta, not silently overwrite.
5. **Branch-name stability across bounces.** PRs anchor on branch names. Today the branch (`agent/<slug>`) stays stable across `human_review → building` bounces, so this is already safe — just calling it out so it doesn't regress.
6. **What `/validate` reruns mean after a `changes_requested` bounce.** If the change is small (typo, missing test), running the full validate stage feels like overkill. But the contract today is that any state advance through `validating` writes fresh `review.md` + `qa/report.md`. Should we allow a `--skip-validate` path on small changes, or require full re-validate every cycle? Lean toward requiring full re-validate but making it cheap — the curated `validate-context.md` (TODO §1) means the reviewer is reading one file, not five.
7. **Multi-round comment thread state.** PR comments accumulate across rounds. After 3 rebuild cycles, `change-request.md` shouldn't be "all comments ever" — it should be "unresolved comments + new comments since last push." `pr-sync` needs to track which comments were addressed (heuristic: comments marked resolved in GitHub, or comments on lines that no longer exist in the new diff) vs. which are still open.

### Tasks

This is large enough that landing it as one TODO is a fiction; it'll be a sub-project across many runs. Listing the unit-of-work breakdown so future runs can pick discrete pieces:

- [ ] Decide between Option A (forked lifecycle, new states) vs. Option B (re-entrant `human_review` with no new states). The conversation that produced this TODO leaned A; revisit before committing because it's the largest schema change to the workbench since pass-1.
- [ ] Add `target.delivery` and `target.delivery_config` fields to `schemas/run-metadata.yaml`. Update the metadata loader (TODO §4 schema validation should land first or co-land to catch typos).
- [ ] Update `schemas/transitions.yaml` with the new states (`publishing`, `in_pr_review`, `changes_requested`, `closed`) and their transition evidence requirements. Decide what evidence each transition needs (e.g. `publishing → in_pr_review` needs `pr_number`, `pr_url`, `branch_pushed_sha`).
- [ ] Build `cmd_publish_pr.py` — the slash command that takes a `publishing`-state run, validates `pr-draft.md` exists and is non-empty, pushes the branch, calls `gh pr create --body-file pr-draft.md --title "$(head -1 pr-draft.md)"`, captures the returned PR number/URL, and transitions to `in_pr_review`. Lots of edge cases (auth, branch already exists on remote, force-push policy).
- [ ] Build `cmd_pr_sync.py` — polls `gh pr view --json` for the current state, emits the right events, transitions if state changed. Idempotent.
- [ ] Build a `publishing`-stage LLM-bearing slash command (`/draft-pr` or extend `/handoff` for `pull-request` runs). Drafts `pr-draft.md` from `HUMAN_REVIEW.md` + brief + review + diff + linked Linear ticket (Linear MCP integration for the ticket fetch).
- [ ] Add the pre-PR adversarial-review sub-step to the `publishing` slash command. Dispatches an Agent-tool subagent (`general-purpose` or `Explore`) fed `validate-context.md` + the diff; subagent returns structured findings; master serializes `adversarial-review.md`. Decide whether to reuse the `/pr-review` skill's `adversarial` mode or fork its prompt into a workbench-owned subagent contract. If any finding is `severity: blocker`, refuse to write `pr-draft.md` and force a bounce to `human_review`.
- [ ] Update `cmd_complete.py` to detect `delivery: pull-request` and take the A1 path (no local merge; just record `merge:<sha>` from the PRMerged event). Make sure the merge-into-master semantics for `local-merge` runs are preserved unchanged.
- [ ] Update `cmd_abandon.py` to prompt about closing an open PR if one exists.
- [ ] Update `cmd_bounce.py` (or add a new bounce path) so PR-comment-driven bounces pre-populate `change-request.md` from PR state — currently `change-request.md` is human-authored. Decide whether `pr-sync` does the population at the event time or whether the bounce command pulls fresh.
- [ ] Board changes — surface PR state (`PR #1234`, approvals count, CI status, last comment time) in `in_pr_review` rows. The board's RunSnapshot model needs new fields; the renderer needs new columns or a status pill.
- [ ] Audit + `HUMAN_REVIEW.md` rendering — `lib.human_review.render` doesn't know about PR state today. Add a `## Pull request` section that renders when `pr_meta` is present.
- [ ] Documentation — `architecture.md` § "Non-goals for V1" currently says "No PR creation." That non-goal moves; document the new non-goals (no auto-merge, no auto-resolve-comments, no auto-assignment of reviewers from CODEOWNERS unless `auto_assign_reviewers` is set).
- [ ] Tests — full E2E coverage for the `pull-request` lifecycle: happy path (draft → publish → approve → merge → done), CR path (publish → CR → rebuild → republish), abandon path (publish → close → closed).

### Acceptance

- A run with `target.delivery: pull-request` flows `... → human_review → publishing → in_pr_review → done` against a real GitHub repo, with the PR created from `pr-draft.md` and `done` triggered by `PRMerged`.
- A reviewer comment on the PR, followed by `pr-sync`, triggers `in_pr_review → changes_requested → building` with `change-request.md` pre-populated from the comment.
- A PR closed without merge transitions to `closed` (new terminal), not `abandoned`.
- The `publishing` stage produces `adversarial-review.md` from a fresh subagent (master session does not Read the diff or prior artifacts during the adversarial pass), and a `severity: blocker` finding blocks `pr-draft.md` from being written.
- `local-merge` runs continue to work exactly as today — no regression in the personal-repo path.
- The board shows distinct rows for `publishing`, `in_pr_review`, `changes_requested`, `closed`.
- `architecture.md` and `docs/lifecycle.md` document the new states and the delivery-mode fork.

### Non-goals (for this TODO; reconsider later)

- Auto-merging PRs even when CI + reviews are green (human runs `/complete` or merges via GitHub UI).
- Auto-resolving review comments (the agent rebuilds against `change-request.md`; resolving the threads on GitHub is the human's call).
- Real-time PR state via webhooks (poll-based `pr-sync` is V1; webhooks are V2).
- Auto-assigning reviewers from CODEOWNERS (opt-in via `delivery_config.auto_assign_reviewers`, off by default).
- Multi-PR runs (one run still maps to one branch maps to one PR).
- Cross-repo PRs / monorepo PR splits — out of scope until the multi-repo run model lands.
- Merge-strategy configurability (squash/rebase/merge) — V1 lets the GitHub repo's settings decide; `gh pr merge` honors them.

### Origin

Surfaced 2026-05-25 by the user after I sketched a too-thin `/publish` slash command in a prior turn. The user pushed back: PR descriptions are not fire-and-forget, the human must see and approve what gets pushed, `done` cannot mean "auto-merged to master" for team work, and the change-request-comments-arrive-later loop needs a real state, not a re-entry into `human_review`. This TODO is the larger redesign that the original sketch glossed over.

---

## 8. Per-run tool-policy allowlist (only relevant once §7 ships)

Today the workbench's safety story is filesystem-via-worktrees + evidence-gated transitions. There's no per-run tool bounding because there's no need — `local_only: true` in `agent-workbench.yaml` means no remote calls, the worktree confines git operations to one branch, and the agent's shell tool is the agent's-harness problem.

§7 changes the threat model. `cmd_publish_pr.py` runs `gh pr create` (pushes the branch, creates a PR against a real GitHub repo). `cmd_pr_sync.py` runs `gh pr view --json …` and `gh api repos/<owner>/<repo>/pulls/<n>/comments`. The architecture statement "Talk to GitHub or any remote API → Agent Workbench does NOT do this" becomes false. The blast radius grew from "the worktree" to "the user's GitHub credentials + every repo they can write to."

The architectural concern: today, an agent inside a `building` stage that decides on its own to run `gh pr create` would succeed (the harness allows `gh`; the workbench doesn't know to stop it). That's wrong even in the `local-merge` world; it becomes a real problem in the `pull-request` world because the agent now has examples of when `gh` calls are valid (during `publishing`) and might generalize.

### Proposed shape

A per-stage tool-policy file declares which commands are allowed during which lifecycle states. Stored alongside the lifecycle schema:

```yaml
# schemas/tool-policy.yaml
schema_version: 1
kind: tool_policy

stage_policies:
  shaping:
    shell_allowlist: []          # no shell calls at all
    network: deny

  planning:
    shell_allowlist:
      - git
      - find
      - grep
      - rg
    network: deny

  building:
    shell_allowlist:
      - git
      - "*"                       # full shell; the worktree is the bound
    network: deny                 # except via explicit tooling (test runners may need it)

  validating:
    shell_allowlist:
      - git
      - "<test-runners>"
      - playwright
    network: allow_for_qa

  # NEW for §7
  publishing:
    shell_allowlist:
      - gh pr view
      - gh pr create
      - gh api repos/*/*/pulls/*
    network: allow_for_github_only
    gh_repo_scope: per_run        # see below

  in_pr_review:
    shell_allowlist:
      - gh pr view
      - gh api repos/*/*/pulls/*
    network: allow_for_github_only
```

`gh_repo_scope: per_run` means: the policy is scoped to the specific `target.repo` of this run. A run targeting `klaviyo/app` cannot use `gh` against `klaviyo/fender` even though the user's credentials cover both.

Two enforcement paths:

1. **Harness-mediated.** The workbench writes a `tool-policy.yaml` per run; the agent's harness (Claude Code, Codex) reads it and refuses tool calls outside the allowlist. This is the practical V1 path — it doesn't need any new infrastructure on the workbench side beyond emitting the policy. Whether each harness honors it is a per-harness contract; Claude Code's settings.json hooks are the closest existing primitive.
2. **Wrapper scripts.** The workbench provides a wrapped `gh` (and similar) in a stage-specific PATH; the wrapper checks the policy before forwarding. Heavier, doesn't depend on the harness, but the agent could bypass by calling `/usr/bin/gh` directly unless we also lock down PATH.

Lean toward path 1 for V1. If the harness can't be trusted, path 2 is the escalation.

This is **not** capability tokens (cryptographically signed, expirable). The mental model is closer to AppArmor / firejail profiles: a static policy file per stage, loaded at stage entry, denying anything not listed. Simpler, no crypto, no token lifecycle.

### Tasks

- [ ] **Do nothing until §7 actually starts.** This is a sequential dependency: tool-policy is only meaningful when remote-calling commands enter the workbench's surface. Pre-§7, the only commands the workbench cares about are `git` (worktree-bounded) and `Read`/`Edit`/`Write` (filesystem-bounded). Adding policy infrastructure now would be premature.
- [ ] **When §7 starts: spec `schemas/tool-policy.yaml`.** Define the stage_policies block above, including the `publishing`/`in_pr_review` entries. Decide whether `gh_repo_scope: per_run` is enforceable via `gh`'s native repo-scoping (`gh repo set-default`) or needs a wrapper.
- [ ] **Decide the enforcement path.** Harness-mediated (path 1) vs. wrapper scripts (path 2). Spike both on a single command (`gh pr view`) before committing to the broader rollout. Document the choice in `architecture.md`.
- [ ] **Add `cmd_doctor.py` checks for policy violations.** `agent-workbench doctor` already validates run integrity; extend it to check whether the events log shows any commands run outside that run's policy. Retrospective audit, not preventative; complements whichever enforcement path is chosen.
- [ ] **Document the contract in `agent-workbench-live/AGENTS.md`.** The agent needs to know "I am in stage X and may only run commands in this allowlist." Make it part of the per-stage rules section in lifecycle.md.

### Acceptance

- §7's `publishing` stage cannot run `gh pr merge` (only allowed commands are `gh pr view`, `gh pr create`, scoped `gh api …`).
- §7's `building` stage (re-entered after a `changes_requested` bounce) cannot push, cannot create a new PR, cannot close the existing one — the publishing-stage policy is not in effect during building.
- A run whose policy file is missing or malformed refuses to start (`doctor` flags it; `transitions.transition` rejects).
- `local-merge` runs continue to work without any policy file (default-allow for that delivery mode, since there's no remote attack surface).

### Non-goals

Capability tokens (no crypto, no expiry, no issuance). Sandboxing the agent's shell tool generally (the worktree is sufficient bound today). Network egress filtering at the OS level (this is a per-command policy, not a network firewall). MCP-server-level policy (out of scope; that's the harness's problem).

### Origin

Surfaced 2026-05-25 in a discussion of agent-workbench's safety mechanisms. Today's bounding is filesystem-via-worktrees + state-machine evidence gates; both work because the workbench is local-only. §7 (PR-flow lifecycle) explicitly punctures the local-only stance by adding `gh`-calling commands. This TODO is the matching safety primitive — a per-run, per-stage allowlist that lets the workbench say "even though the agent could call X, in this stage of this run it cannot."

---

## 9. Subagent cost measurement — verify `metrics.jsonl` captures subagent token spend

`lib/metrics/writer.record_run_metrics` writes `metrics.jsonl` at the validate / followups / abandon boundaries. The intent is to attribute token spend to the run. The open question: when a stage spawns a Claude Code Agent-tool subagent (an `Explore` for read-heavy lookup, a `Plan` for design, a `general-purpose` for fan-out), **is the subagent's token spend captured in `metrics.jsonl`, or is only the master session's spend recorded?**

This isn't a correctness concern about the agent's behavior — subagents should keep being spawned, the architecture says they should, and they're how the workbench keeps the master session's prefix bounded (see AGENTS.md "Subagent-first read strategy"). It's an accounting concern: if subagent spend isn't attributed to the run, then any run that fans out heavily looks artificially cheap, and cross-run comparisons (which the board surfaces) are misleading.

### Tasks

- [ ] **Read `lib/metrics/writer.py` + `lib/metrics/buckets.py` + the bucket sources to determine what counts as "input/output tokens" for a run.** The relevant question: does the underlying telemetry source (whatever the writer pulls from — `claude-code session metrics`, the Anthropic API ledger, something else?) include nested-Agent-tool calls in the parent session's totals, or are they tracked separately?
- [ ] **Write a synthetic run that explicitly spawns N Agent-tool subagents from `/validate` and compare the resulting `metrics.jsonl` against the master-session-only baseline.** If the subagent spend is invisible, the delta will be small / zero; if it's captured, it'll match the subagents' individual spend.
- [ ] **If subagent spend is NOT captured: extend the writer.** This may require the writer to read from a more comprehensive source, or to walk subagent IDs and sum them. Implementation depends entirely on the telemetry source's shape — investigate first, design after.
- [ ] **If subagent spend IS captured but not labeled: add a `subagent_spend` rollup to the metrics.** Even if the totals are correct, knowing "how much of this run's spend was master vs. subagent" is useful diagnostic information for tuning the subagent-first strategy.
- [ ] **Document the contract.** Whatever the answer turns out to be, write it in `lib/metrics/writer.py`'s module docstring and link from `agent-workbench-live/AGENTS.md` § "Subagent discipline" so the next person isn't unsure what they're looking at.

### Acceptance

- A test or measurement script demonstrates whether subagent tokens are captured in `metrics.jsonl`. Answer is one of: (a) yes, captured in totals, (b) yes, captured separately, (c) no, missing.
- If (c), the writer is updated and the next test run shows the spend included. If (a) or (b), the docstring documents which case applies.
- The board's per-run spend display (if it shows a token total) is accurate within ~5% of the true total including subagent work.

### Non-goals

Throttling, capping, or denying subagent spawn — the policy is "spawn subagents when the work justifies it, and measure honestly." This TODO is purely measurement. Building a per-subagent breakdown in the audit (e.g. "this run spawned 3 Explore subagents, here's what each cost") would be nice but is a follow-on; the immediate concern is total-accuracy.

### Origin

Surfaced 2026-05-25 in a design conversation about subagent cost. The architecture explicitly permits subagent spawning and the AGENTS.md "subagent-first read strategy" actively encourages it for read-heavy work. The question of whether the resulting spend is captured in the workbench's own metrics is open — the writer code may or may not pull from a telemetry source that includes nested calls, and verifying this is a small but real piece of work. The concern is cross-run comparability: if fan-out runs look artificially cheap, the board's metrics column lies, and decisions about session boundaries (the validate-cut, the cache-discipline rules) get made against bad data.
