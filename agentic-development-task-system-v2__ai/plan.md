# Plan — Renovate Task Workflow, Pass 1 (Track 1: 1a + 1b + 1c)

## Brief

Land the foundation of TODO §1 (Renovate task workflow): the on-disk reshape (`stages/` + `archive/`), the file mergers (`build.md`, `plan.md` with folded sections), and `HUMAN_REVIEW.md` as the new reviewer entry point. Defer 1d–1g to follow-up passes.

**Confirmed decisions (this pass):**

- **Scope:** 1a (layout) + 1b (mergers) + 1c (HUMAN_REVIEW.md). 1d–1g deferred.
- **Back-compat:** existing flat-layout runs (e.g. `runs/2026-05-18-poker/`) remain readable but never rewritten. New runs use the new layout.
- **Architecture:** new module `agent-workbench-live/lib/lifecycle.py` owns stage directory placement, archiving on supersession, and pruning. The transition engine calls into it after a successful `metadata_mod.set_status`.
- **Evidence keys:** unchanged. Their *values* now point under `stages/<stage>/`. `events.jsonl` readers don't break.
- **Move timing:** on transition *into the next stage*. Commands keep writing where they write today; the engine moves them as the stage closes.
- **Supersession:** only `human_review → building` (bounce) archives the prior `stages/building/` and `stages/validating/` to `archive/`. Brief-level supersession deferred.
- **Enforcement:** `validating → human_review` requires `HUMAN_REVIEW.md` to exist and contain the literal headings `## Suggested first checks` and `## Run timeline`. Section-shape parsing deferred.

**New canonical layout for runs created after this change:**

```
runs/<run_id>/
  stages/
    draft/raw-idea.md
    shaping/brief.md
    planning/plan.md            # folds preflight + decisions/assumptions
    building/build.md           # merges implementation-summary + diff-summary
    validating/review.md
    validating/qa/...
  archive/
    building/build-v1.md         (only on bounce supersession)
    validating/review-v1.md      (only on bounce supersession)
    validating/qa-v1/            (only on bounce supersession)
  HUMAN_REVIEW.md               # replaces handoff.md; contains "Suggested first checks" + "Run timeline"
  metadata.yaml
  events.jsonl
```

Top-level entries for a clean, completed run: **5** (`stages/`, `HUMAN_REVIEW.md`, `metadata.yaml`, `events.jsonl`, and `archive/` only if non-empty). Empty `archive/` is pruned on the `validating → human_review` transition.

## Changes

### 1. New module: `lib/lifecycle.py`

Owns the on-disk reshape. Public surface:

```python
# Layout helpers
LAYOUT_FLAT = "flat"
LAYOUT_STAGED = "staged"

def detect_layout(cfg, run_id) -> str
    # returns LAYOUT_STAGED if runs/<id>/stages/ exists, else LAYOUT_FLAT
def is_staged_run(cfg, run_id) -> bool
def stage_dir(cfg, run_id, stage) -> Path
    # runs/<id>/stages/<stage>/
def archive_dir(cfg, run_id, stage) -> Path
    # runs/<id>/archive/<stage>/

# Stage layout
def init_staged_layout(cfg, run_id) -> None
    # Called by `new-run` for fresh runs. mkdir runs/<id>/stages/.

# Move-on-transition: called by transition engine after set_status.
def on_transition(cfg, run_id, from_state, to_state, evidence) -> dict
    # Performs per-stage promote and (for bounce) archive moves.
    # Returns a dict of {old_path: new_path} rewrites to apply to evidence
    # before the TransitionApplied event is emitted.

# Supersession on bounce
def archive_for_bounce(cfg, run_id) -> list[Path]
    # Moves stages/building/ -> archive/building/build-v<N>.md
    # and    stages/validating/ -> archive/validating/<file>-v<N>.md
    # Picks N by counting existing -v<N> files. Returns list of moved paths.

# Pruning
def prune_empty_dirs(cfg, run_id) -> None
    # Removes any empty subtree under stages/, archive/, qa/.

# HUMAN_REVIEW.md helpers (used by command + validator)
def human_review_path(cfg, run_id) -> Path
def validate_human_review_sections(cfg, run_id) -> list[str]
    # Returns list of missing-heading error strings; empty list = OK.
```

Per-stage promote map (evidence key → target path under `stages/`):

| from_state → to_state | Move(s)                                                                                                  |
|-----------------------|----------------------------------------------------------------------------------------------------------|
| draft → shaping       | `raw-idea.md` → `stages/draft/raw-idea.md`                                                               |
| shaping → planning    | `brief.md` → `stages/shaping/brief.md`                                                                   |
| planning → ready      | `plan.md` (merged) → `stages/planning/plan.md`; old `preflight.md`/`assumptions.md`/`decisions.md` deleted from run root if they exist (their content has been folded — see §2 below) |
| ready → building      | No moves (no new outputs at this hop; just worktree create).                                             |
| building → validating | `build.md` → `stages/building/build.md`                                                                  |
| validating → human_review | `review.md` → `stages/validating/review.md`; `qa/` → `stages/validating/qa/`; ensure `HUMAN_REVIEW.md` exists with required sections; prune empty dirs |
| human_review → building (bounce) | Archive current stages/building/ and stages/validating/ to archive/<stage>/<file>-v<N>.md; new build resumes empty |
| any → done            | No moves. (Files already promoted by earlier transitions.)                                               |
| any → abandoned       | No moves. (Preserve current state.)                                                                      |

### 2. CLI command changes

The 1b mergers happen in the commands that *produce* the merged file:

- **`lib/cli/plan.py`** — instead of writing `plan.md`, `assumptions.md`, `decisions.md`, `preflight.md` as four files, write a single `plan.md` with four sections (`Plan`, `Preflight`, `Decisions & assumptions`, etc.). Evidence keys `assumptions_path`, `decisions_path`, `preflight_path` still get filled — they point at `plan.md` with `#section-anchor` fragments. This keeps `transitions.yaml` evidence requirements intact while telling readers where in `plan.md` to look.

  Concretely, evidence for `planning → ready` becomes:
  - `plan_path: stages/planning/plan.md`
  - `assumptions_path: stages/planning/plan.md#decisions--assumptions`
  - `decisions_path: stages/planning/plan.md#decisions--assumptions`
  - `preflight_path: stages/planning/plan.md#preflight`

- **`lib/cli/validate.py`** / build command — builder writes a single `build.md` (template-driven, see below) with the required sections. Evidence `implementation_summary_path` and `diff_summary_path` both point at `stages/building/build.md` (with anchors).

- **`lib/cli/handoff.py`** — writes `HUMAN_REVIEW.md` (at run root) instead of `handoff.md`. Evidence `handoff_path` points at `HUMAN_REVIEW.md`. Section validator from `lifecycle.validate_human_review_sections` is invoked before emitting `TransitionApplied` for `validating → human_review`; missing sections raise `TransitionError`.

- **`lib/cli/new_run.py`** — calls `lifecycle.init_staged_layout` so fresh runs start with `stages/` already created.

- **`lib/cli/bounce.py`** — calls `lifecycle.archive_for_bounce` before transition.

### 3. Templates

Update `agent-workbench-live/templates/`:

- **`plan.md`** — extend with merged sections: `## Plan`, `## Preflight`, `## Decisions & assumptions`. (Keep existing `plan.md` body; add the headings + brief authoring guidance.)
- **`build.md`** — NEW. Merges `implementation-summary.md` + `diff-summary.md`. Sections: `## What changed`, `## Files changed`, `## Reviewer reading order`, `## Acceptance criteria coverage`, `## Deviations from plan`, `## Known issues`, `## Commands run`. (`Documentation touched` lives in 1d, not this pass — but include the section as `_(filled in 1d)_` placeholder? **Decision: omit. Will add when 1d lands.**)
- **`HUMAN_REVIEW.md`** — NEW. Skeleton with the persona-keyed hub, `## Suggested first checks`, and `## Run timeline` sections.

Leave `assumptions.md`, `decisions.md`, `preflight.md`, `implementation-summary.md`, `diff-summary.md`, `handoff.md` template files in place. They're still referenced by old-layout runs and by code paths we haven't yet rewired. They become dead code only once 1b is fully done across the CLI — we'll delete in a later pass.

### 4. Transition engine wiring

In `lib/transitions.py`, after the successful `set_status` and before emitting `TransitionApplied`:

```python
# After: metadata_mod.set_status(cfg, run_id, to_state)
if lifecycle.is_staged_run(cfg, run_id):
    rewrites = lifecycle.on_transition(cfg, run_id, from_state, to_state, evidence)
    # Apply rewrites to the evidence dict in-place so the event records the
    # post-move paths.
    for k, new_path in rewrites.items():
        if k in evidence:
            evidence[k] = new_path
```

For old (flat) runs, `is_staged_run` returns False and nothing changes. This is the entire back-compat story.

Add a section-validation step inside `transition(...)` specifically for `validating → human_review` on staged runs: call `lifecycle.validate_human_review_sections` and raise `TransitionError` with the list of missing headings if any.

### 5. AGENTS.md / README.md / docs/lifecycle.md

- `docs/lifecycle.md`: add a paragraph documenting the new layout, the back-compat rule (old runs stay flat), and the bounce-supersession archive rule.
- `agent-workbench-live/AGENTS.md`: update the per-stage "produces" line to point at `stages/<stage>/`.
- `agent-workbench-live/README.md`: update the example directory tree.

## Tests

### Unit (new in `tests/test_lifecycle.py`)

- `test_detect_layout_flat` — a run with no `stages/` directory returns `LAYOUT_FLAT`.
- `test_detect_layout_staged` — a run with `stages/` returns `LAYOUT_STAGED`.
- `test_init_staged_layout_creates_dirs` — `init_staged_layout` creates `stages/`.
- `test_on_transition_shaping_to_planning_moves_brief` — `brief.md` at run root is moved to `stages/shaping/brief.md`; returned rewrites map reflects the new path.
- `test_on_transition_idempotent` — calling `on_transition` twice doesn't double-move.
- `test_archive_for_bounce_versions_correctly` — first bounce produces `archive/building/build-v1.md`; second bounce produces `-v2.md`.
- `test_archive_for_bounce_moves_validating_dir` — `stages/validating/qa/` → `archive/validating/qa-v1/`.
- `test_prune_empty_dirs_removes_empty_archive` — empty `archive/` directory is removed on `validating → human_review`.
- `test_validate_human_review_sections_missing` — missing `## Suggested first checks` returns the heading in the missing list.
- `test_validate_human_review_sections_ok` — both required headings present returns `[]`.

### Unit (extend `tests/test_transitions.py`)

- `test_transition_validating_to_human_review_rejects_missing_human_review_sections` — staged run with a `HUMAN_REVIEW.md` that lacks `## Suggested first checks` fails the transition. `TransitionRejected` event is emitted.
- `test_transition_engine_rewrites_evidence_paths_on_staged_run` — after `shaping → planning`, the recorded `TransitionApplied.payload.evidence.brief_path` equals `stages/shaping/brief.md`.
- `test_transition_engine_is_noop_on_flat_run` — a flat-layout run transitions identically to before; no `stages/` directory is created.

### Integration (extend `tests/test_integration.py`)

- `test_happy_path_staged_layout` — fresh `new-run` → drive through to `human_review`. Assert top-level entries are exactly `{stages, HUMAN_REVIEW.md, metadata.yaml, events.jsonl}` and `stages/shaping/brief.md`, `stages/planning/plan.md`, `stages/building/build.md`, `stages/validating/review.md` exist.
- `test_bounce_loop_archives_prior_build` — after `validate → bounce → validate → complete`, `archive/building/build-v1.md` and `archive/validating/review-v1.md` exist, and `stages/building/build.md` contains the post-bounce content.
- `test_old_flat_run_still_loads` — fixture mimicking `runs/2026-05-18-poker/`'s flat layout: `agent-workbench show <id>` and `events <id>` work without error and don't create a `stages/` directory.

### Manual

- Inspect `runs/2026-05-18-poker/` after running the test suite: contents unchanged.
- Create a fresh run end-to-end (`/new-run` → … → `/handoff`); open the run directory and confirm: 5 top-level entries (or 4 if no bounce), `HUMAN_REVIEW.md` contains both required sections, anchors in `plan.md` resolve in a markdown viewer.

## Out of scope (deferred to later passes)

- 1d: `## Documentation touched` section in `build.md` + adversarial doc-claim verification.
- 1e: `build_iterations`, `build_exit_reason`, `max_build_iterations` in `metadata.yaml`.
- 1f: new `followups` stage and `follow-ups.md`. Lifecycle stays `draft → shaping → planning → ready → building → validating → human_review → done/abandoned`.
- 1g: blast-radius section in `review.md`.
- Brief-level supersession on `/bounce` (deferred per the "implement supersession for bounce-from-human_review only" decision).
- Deleting now-redundant templates (`assumptions.md`, `decisions.md`, `preflight.md`, `implementation-summary.md`, `diff-summary.md`, `handoff.md`). They stay until follow-up passes prove nothing references them.
