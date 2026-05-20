# Plan — Renovate Task Workflow, Pass 3 (TODO §1f)

## Brief

Insert a new lifecycle stage, `followups`, between `validating` and `human_review`. The stage authors a single forward-looking file — `stages/followups/follow-ups.md` — listing 1–5 candidate next-run ideas (or one explicit "no follow-ups identified" entry). **No execution.** This pass writes the file; the stretch `agent-workbench followup spawn` command stays deferred.

**Confirmed decisions:**

- **Scope:** §1f only. §1g lands in pass 4 as a separate commit.
- **Authoring path:** dedicated `agent-workbench followups` CLI + `/followups` slash command. `--init` transitions `validating → followups` and stages `follow-ups.md` from a template at run root for the LLM to fill. Default mode validates the file, applies the move-on-transition into `stages/followups/`, and transitions `followups → human_review`.
- **Strictness:** the `followups → human_review` gate requires `follow-ups.md` to exist, be non-empty, and have YAML frontmatter on every entry with the 5-category enum. "No follow-ups identified" is written as one explicit entry with that category (per TODO §1f).

## Changes

### 1. State machine (`schemas/transitions.yaml`)

- Add `followups` to `states.non_terminal`.
- Replace the existing `validating → human_review` transition with `validating → followups`, then add a new `followups → human_review`. Evidence requirements migrate to the followups transition where they make sense (most stay on the new `followups → human_review` since that's the gate the reviewer actually lands at).
- Update `wildcard_transitions` (`any_non_terminal → abandoned`) — already wildcard, no edit needed.

Concretely:

```yaml
states:
  non_terminal:
    - draft
    - shaping
    - planning
    - ready
    - building
    - validating
    - followups     # NEW
    - human_review

transitions:
  # existing draft -> shaping … building -> validating unchanged
  - from: validating
    to: followups
    description: Self-review and QA are complete; now brainstorm forward-looking follow-ups.
    evidence:
      required:
        - review_report_path
        - qa_report_path
        - audit_path
      optional:
        - tests_passed
        - known_issues_count
        - qa_recording_path
        - qa_trace_path
    emits:
      - TransitionApplied

  - from: followups
    to: human_review
    description: Follow-up candidates are recorded; local branch and worktree ready for human review.
    evidence:
      required:
        - followups_path
        - handoff_path
        - branch_name
        - worktree_path
      optional:
        - audit_path
    emits:
      - TransitionApplied
```

The old `validating → human_review` rule is **removed**. Tests that drove validating directly to human_review have to add the followups hop.

### 2. metadata.py

Add `"followups"` to `STATUSES`. Add a new field-by-default to the `create()` metadata template:

```python
"artifacts": {
    ...
    "followups": None,     # NEW (set when --init stages the template)
    ...
},
```

This keeps the existing "artifact path lives in the artifacts block" pattern.

### 3. lifecycle.py — promote follow-ups.md

Extend `_STAGE_OUTPUTS` so the `followups` stage's output gets promoted on `followups → human_review`:

```python
"followups": [
    ("followups_path", "follow-ups.md", "followups", "follow-ups.md"),
],
```

No new anchor-evidence keys needed.

### 4. New module: `lib/followups.py`

Owns the frontmatter parser + validator. Public surface:

```python
NONE_IDENTIFIED_CATEGORY = "no_followups"   # the explicit-opt-out entry

VALID_CATEGORIES = {
    "tech_debt", "scope_extension", "bug_risk",
    "refactor", "docs", "deferred_from_bounce",
    "no_followups",   # sentinel for explicit "none identified"
}

REQUIRED_FRONTMATTER_KEYS = ("title", "motivation", "suggested_scope", "category")

def extract_entries(md_text) -> list[dict]
    # Split on `---\n…\n---` blocks; parse YAML-ish frontmatter into dicts.

def validate(md_text) -> list[str]
    # Returns list of error strings; empty = OK.
    # Errors: no entries; entry missing key; category not in enum; etc.
```

The parser uses the existing `lib.yaml_io` for the YAML body (subset-friendly). Frontmatter blocks are anywhere in the file separated by `---`; an "entry" is one frontmatter block plus the prose that follows it until the next block.

### 5. New CLI command: `lib/cli/cmd_followups.py`

```text
agent-workbench followups <run_id> --init
    Transition validating -> followups. Stages follow-ups.md from
    templates/follow-ups.md at the run root.

agent-workbench followups <run_id>
    Validate follow-ups.md (validators from lib/followups.validate).
    Transition followups -> human_review.
```

Both modes write `metadata.artifacts.followups = "stages/followups/follow-ups.md"` (after the transition for default mode, where the engine has just moved the file). Emit a `FollowupsRecorded` event in default mode with `{path, entry_count, categories}`.

### 6. `cmd_validate.py` retargets to `followups`

The default-mode `validate` currently runs `validating → human_review` and does ReviewCompleted / QACompleted / AuditRendered / HumanHandoffCreated / DocClaimsVerified. It now runs `validating → followups` instead and **moves the HumanHandoffCreated emission + the HUMAN_REVIEW.md section gate to the new `followups → human_review` transition** (since that's when the reviewer actually lands).

Two practical consequences:
- HUMAN_REVIEW.md doesn't have to exist at `validate` time. It only has to exist when `followups` is finalized.
- The transition-engine gate `validate_human_review_sections` (added in pass 1) now fires on `followups → human_review`, not `validating → human_review`.

### 7. New event: `FollowupsRecorded`

`schemas/events.jsonl`:

```jsonl
{"kind":"event_schema","event_type":"FollowupsRecorded","required_fields":[…],"payload_required":["followups_path","entry_count","categories"],"payload_optional":["note"]}
```

### 8. New template: `templates/follow-ups.md`

YAML-frontmatter format example, with 3 sample entries. Reviewer-facing comments explain category meanings.

### 9. New slash command: `.claude/commands/followups.md`

Thin wrapper — calls `agent-workbench followups` `--init`, instructs the LLM to author 1–5 mini-briefs reading `stages/{building,validating,planning}` + `events.jsonl` (filtered to BounceRequested) + any prior `archive/` briefs, writes `follow-ups.md`, then calls the default-mode CLI to finalize.

### 10. HUMAN_REVIEW.md template updates

Wire the "Want to see what's next?" hub line to point at the new file (`stages/followups/follow-ups.md`). This was already a placeholder in pass 1's template.

## Tests

### Unit
- `tests/test_followups.py`:
  - `test_extract_no_blocks_returns_empty`
  - `test_extract_one_entry`
  - `test_extract_multiple_entries`
  - `test_validate_rejects_empty_file`
  - `test_validate_rejects_missing_required_key`
  - `test_validate_rejects_invalid_category`
  - `test_validate_accepts_no_followups_sentinel`
  - `test_validate_accepts_all_5_real_categories`
- `tests/test_transitions.py`:
  - Update `_evidence_for` for the new transitions.
  - `test_validating_directly_to_human_review_rejected` — the old direct path no longer exists.
  - `test_followups_to_human_review_requires_followups_path`
  - `test_followups_to_human_review_requires_human_review_sections` — the existing gate now fires here, not on the validating hop.

### Integration
- Update `test_full_lifecycle` to add a `/followups` hop:
  - After `validate` (now: validating → followups), write `follow-ups.md` at run root with two real entries.
  - Run `followups` (default mode), which transitions to `human_review`.
  - Assert `stages/followups/follow-ups.md` exists and the top-level entries are exactly `{stages, HUMAN_REVIEW.md, metadata.yaml, events.jsonl, audit.md}`.
- Update the bounce-loop test the same way.

## Out of scope (still deferred)

- §1g (blast-radius in review.md) — separate commit in pass 4.
- `agent-workbench followup spawn <run_id> <n>` (TODO §1f stretch) — creates a new draft run from a chosen mini-brief.
- Migration / back-compat for any in-flight runs already in `validating` (none exist in practice; the only real run is `2026-05-18-poker` which is already in `human_review` on the flat layout — completely untouched).
