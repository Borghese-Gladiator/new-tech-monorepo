# Plan — Renovate Task Workflow, Pass 2 (TODO §1d + §1e)

## Brief

Build on pass 1 (committed in `d1d8b44`). This pass surfaces two things that ran invisibly inside `building` before: the build/test iteration loop, and changes the run made to the target repo's own docs. Layout is unchanged.

**Confirmed decisions:**

- **Scope:** §1d (Documentation touched) + §1e (build-loop metadata). §1f and §1g deferred.
- **1e strictness:** `building → validating` rejects when metadata lacks `build_iterations` or `build_exit_reason`. `validate --init` fills defaults (`build_iterations=1`, `build_exit_reason=tests_green`) when the builder hasn't written them — the human sees the defaults in `HUMAN_REVIEW.md` and can challenge them.
- **1d verification:** `validate` default mode parses `build.md`'s "Documentation touched" section, runs `git diff --name-only <base_ref>..HEAD` in the target worktree, and flags discrepancies in `review.md`. False claims ("updated README" with README unchanged) become review findings, not silent passes.

## Changes

### 1. Metadata schema (1e)

Add three fields to the run's metadata.yaml:

```yaml
build:
  iterations: <int>        # how many builder test/fix cycles ran
  exit_reason: <enum>      # tests_green | max_iterations_hit | hard_block | manual_stop
  max_iterations: <int>    # caller's iteration ceiling for this run (default 5)
```

Place these at top-level next to `validation:` and `completion:`. Why a new `build:` block (vs. inline keys): groups related fields, mirrors the existing `validation:` / `completion:` shape, room to grow (1f's `followups:` will land alongside).

- Update `lib/metadata.py`:
  - Extend `REQUIRED_TOP_LEVEL` with `"build"` for **new** runs only (`metadata.create` writes it). Existing flat-layout runs lack the key — `metadata.load` must not require it for back-compat. **Decision:** add `build` to the `create()` template but keep `REQUIRED_TOP_LEVEL` as-is. Validation continues to check the original keys; the new keys are optional in `_validate`.
  - `metadata.create()` writes `build: {iterations: null, exit_reason: null, max_iterations: 5}` for new runs.
- Update `agent-workbench.yaml`: new `defaults.max_build_iterations: 5` so it's configurable per workbench (overridden per-run via metadata).

### 2. Transition gate (1e)

Add evidence requirements to `schemas/transitions.yaml` for `building → validating`:

```yaml
- from: building
  to: validating
  evidence:
    required:
      - implementation_summary_path
      - diff_summary_path
      - build_iterations     # NEW
      - build_exit_reason    # NEW
```

The schema validator already rejects missing required evidence; no engine change needed beyond fixing whoever populates the evidence.

- Update `lib/cli/cmd_validate.py` `--init` to read `build:` from metadata. If `iterations` is null, default it to `1`; if `exit_reason` is null, default it to `"tests_green"`. Write the defaults back to metadata before the transition, then include the values in the evidence dict.
- Tests covering: missing → defaults filled; pre-set value preserved; transition rejects when metadata lacks the `build:` block entirely (back-compat path for old runs that try to advance — shouldn't happen in practice, but defensive).

### 3. Build report — "Documentation touched" section (1d)

- Add `## Documentation touched` to `templates/build.md`. Two valid forms:
  1. A bulleted list of `<repo-relative path> — <one-line what changed>`.
  2. A single line `none needed — <reason>` (the explicit-skip escape hatch).
- Update `lib/cli/cmd_validate.py` default mode (the validating → human_review path):
  - Read `stages/building/build.md` for staged runs (or run-root `build.md` for flat, though flat runs won't have this section).
  - Extract the "Documentation touched" section.
  - Parse referenced paths: bullets starting with `-`, first whitespace-delimited token is the path.
  - Skip enforcement entirely if the section reads `none needed`.
  - Run `git diff --name-only <base_ref>...HEAD` in the **worktree** (`meta["target"]["worktree"]["path"]`). Collect changed file paths (worktree-relative).
  - For each claimed path: if not in the diff, append a finding to `stages/validating/review.md` under a new `## Documentation claims` section. Don't fail the transition — surface to the reviewer.
  - Emit a `DocClaimsVerified` event with `{claimed: [...], unverified: [...]}`.

New event type to add to `schemas/events.jsonl`:

```jsonl
{"kind": "event_schema", "event_type": "DocClaimsVerified", "required_fields": ["claimed", "unverified"]}
```

### 4. CLI command updates

- `cmd_validate.py --init` (1e):
  - For staged runs, fill build defaults in metadata if missing; include `build_iterations` and `build_exit_reason` in the transition evidence.
- `cmd_validate.py` default mode (1d):
  - Add `_verify_doc_claims(cfg, rd, meta, staged)` helper. Returns `(claimed_paths, unverified_paths)`.
  - Append findings section to `review.md` if `unverified_paths` non-empty.
  - Emit `DocClaimsVerified` event.

### 5. HUMAN_REVIEW.md surface (1e)

§1e calls for a one-line build-loop summary in `HUMAN_REVIEW.md`'s "Run timeline" section ("Build ran N iterations, exited with reason X."). For this pass:

- The template already has a `## Run timeline` placeholder. The validating agent fills it. **Decision:** extend `templates/HUMAN_REVIEW.md` with a `<!-- Build: N iterations, exited with reason X. -->` HTML comment hint inside the Run timeline section. No code-driven injection yet (would require an extra writer pass; defer to a later track).

## Tests

### Unit

- `tests/test_metadata.py`:
  - `test_create_includes_build_block` — new metadata has `build: {iterations: null, exit_reason: null, max_iterations: 5}`.
  - `test_load_backcompat_no_build_block` — a hand-written flat-layout metadata.yaml without `build:` still loads (no MetadataError).
- `tests/test_transitions.py`:
  - `test_building_to_validating_rejects_missing_build_evidence` — transition without `build_iterations` raises TransitionError.
  - `test_building_to_validating_accepts_build_evidence` — transition with the new evidence keys succeeds.
- New `tests/test_doc_claims.py`:
  - `test_extract_doc_section_returns_paths` — parser pulls bullets out of the "Documentation touched" section.
  - `test_extract_doc_section_none_needed` — returns the sentinel `NONE_NEEDED` when the section reads `none needed - ...`.
  - `test_extract_doc_section_missing_returns_empty` — section absent → no claims, no findings.

### Integration

- Extend `test_full_lifecycle` to:
  - Write `build.md` with a "Documentation touched" section claiming `README.md` was updated, while making no actual changes to README.md in the worktree.
  - After `validate`, assert that `stages/validating/review.md` contains a `## Documentation claims` section listing `README.md` as unverified.
  - Assert `metadata.yaml` has `build: {iterations: ..., exit_reason: ..., max_iterations: 5}` after `validate --init`.
  - Assert a `DocClaimsVerified` event was emitted.

## Out of scope (still deferred)

- §1f (new `followups` stage).
- §1g (blast-radius in review.md).
- Wiring the build-loop summary line into HUMAN_REVIEW.md's Run timeline programmatically (template hint only).
- Brief-level supersession on `/bounce`.
