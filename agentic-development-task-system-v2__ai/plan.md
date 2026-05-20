# Plan — Renovate Task Workflow, Pass 4 (TODO §1g)

## Brief

Final Renovate piece. Add a blast-radius signal to `review.md` so reviewers catch scope creep before merge.

**Two complementary mechanisms:**

1. **LLM-authored `## Blast radius` section** (in review.md, during `/validate` step 3). The reviewer agent uses `git` commands inside the worktree to traverse depth-3 callers and write the section itself. The CLI does not pre-compute this — it only instructs the LLM how.
2. **CLI-appended `## Scope creep check` section** (programmatic, by `validate` default mode). Parses `brief.md`'s expected-files section, compares against `git diff --name-only <base>...HEAD`, and lists any diff files not anticipated by the brief.

This mirrors the §1d split: mechanical comparison stays in the CLI, narrative analysis stays in the agent.

## Changes

### 1. New module: `lib/scope_check.py`

Public surface:

```python
EXPECTED_FILE_SECTION_HEADINGS = (
    "Files likely to change",
    "Files to change",
    "Scope",
)

def extract_expected_files(brief_md_text: str) -> list[str] | None
    # Find a matching ## heading, parse bullet paths under it. None means no
    # such section in the brief (signal: skip the check; can't reason about it).

def detect_creep(expected: list[str], actual: list[str]) -> list[str]
    # Return the subset of `actual` not in `expected`. Path matching is
    # permissive: an entry like "src/foo/" matches any actual path that
    # starts with that prefix; "*.md" globs are honored.
```

`extract_expected_files` returns:
- `None` if no matching heading exists in the brief (caller should skip — the brief didn't make a claim, so there's nothing to compare against).
- An empty list `[]` if the heading exists but the section body has no bullets (treated as "brief expected zero files" — every actual diff file is creep).
- A list of paths otherwise.

Path matching rules in `detect_creep`:
- Exact-path match: equal strings.
- Prefix match: if the expected entry ends with `/`, any actual path starting with it counts.
- Glob match: `fnmatch.fnmatch` is used so `src/**/*.py` and `*.md` work.

### 2. CLI integration in `cmd_validate.py`

In the default-mode `validate` (staged runs only, same place §1d's doc-claim check fires):

```python
_check_scope_creep(cfg, rd, meta, actor)  # NEW
_verify_doc_claims_staged(cfg, run_id, rd, meta, actor)  # existing
```

The helper:
- Reads `stages/shaping/brief.md` (the canonical brief at this point — already moved by pass 1).
- Calls `scope_check.extract_expected_files`. If `None`, no event, no review.md append, return.
- Runs `git diff --name-only <base_ref>...HEAD` in `meta["target"]["worktree"]["path"]`.
- Calls `scope_check.detect_creep`.
- If creep non-empty: append a `## Scope creep check` section to `review.md` at run root (before the move). Lists each unexpected file with a one-line reviewer prompt.
- Emits a `ScopeCreepChecked` event with `{expected, actual, creep}`.

### 3. New event: `ScopeCreepChecked`

`schemas/events.jsonl`:

```jsonl
{"kind":"event_schema","event_type":"ScopeCreepChecked","required_fields":[…],"payload_required":["expected","actual","creep"],"payload_optional":["note","base_ref","worktree_path"]}
```

### 4. `/validate` slash command — instruct the LLM to author Blast radius

Edit `agent-workbench-live/.claude/commands/validate.md` Step 3 (the review step). Add a sub-step to author the `## Blast radius` section:

> Run from the worktree:
>   ```
>   git diff --name-only <base_ref>...HEAD
>   ```
>
> For each touched file, identify the top-level symbols (functions, classes, exports) modified in this diff. For each modified symbol:
>   ```
>   git grep -n <symbol>     # depth-2 callers
>   ```
>   Then repeat for the callers of those callers, **stopping at depth 3.**
>
> Write a `## Blast radius` section in `review.md` with a tree like:
>
> ```
> ## Blast radius
>
> depth 1 (changed files):
>   src/foo.py
>   src/bar.py
>
> depth 2 (callers of changed symbols):
>   src/foo.py:fn_x → callers: src/baz.py, src/quux.py
>   …
>
> depth 3 (callers of those callers):
>   src/baz.py:fn_y → callers: tests/test_e2e.py
>   …
> ```
>
> If depth-2 or depth-3 includes files outside the brief's expected scope, call it out as scope creep in this section too.

### 5. `templates/review.md` — placeholder heading

Add a `## Blast radius` placeholder so the section is visible even if the LLM skips it (reviewer can see the empty placeholder and complain).

## Tests

### Unit (`tests/test_scope_check.py`)
- `test_extract_expected_files_returns_none_when_no_section`
- `test_extract_expected_files_returns_empty_for_empty_section`
- `test_extract_expected_files_returns_paths_under_files_likely_to_change`
- `test_extract_expected_files_accepts_alt_headings` (Files to change, Scope)
- `test_detect_creep_exact_match`
- `test_detect_creep_prefix_match`
- `test_detect_creep_glob_match`
- `test_detect_creep_finds_unexpected`
- `test_detect_creep_empty_expected_means_all_actual_are_creep`

### Integration
- Extend `test_full_lifecycle`: the brief has a `## Files likely to change` section listing one file; the actual diff touches a different file. Assert review.md (now at `stages/validating/review.md`) contains a `## Scope creep check` section listing the unexpected file. Assert a `ScopeCreepChecked` event was emitted.

## Out of scope (deferred)

- Depth-2/3 caller graph in the CLI. Per the decision, the agent computes that via `git` itself.
- Renaming the existing review-template `## Blast radius` placeholder to anything richer; that's free-form prose for the agent.
- Configurable depth or stricter scope-creep policy. TODO §1g pins depth at 3 for V1.

## After this lands

All seven Renovate subsections (1a–1g) are complete. The Renovate work for TODO §1 is done; TODO file should advance §2 (Better worktree name) to the top of the remaining queue.
