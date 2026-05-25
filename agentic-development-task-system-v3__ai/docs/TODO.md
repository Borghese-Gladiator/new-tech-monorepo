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

## 2. Board freshness across worktrees after TODO §1

### Why this is here

TODO §1 moved live run dirs into their worktrees (`<worktree>/agent-workbench-live/runs/<id>/`), but the board's freshness infrastructure was scoped to master's `cfg.runs_path` only. Two coupled gaps remain, both surfaced 2026-05-25 while watching the board during this run's own `complete`:

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
