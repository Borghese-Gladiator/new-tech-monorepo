# Plan — TODO #1 (numbered stage dirs) + dogfood follow-ups

## Brief

Implement TODO #1 (number stage directories by execution order) plus the
four follow-ups surfaced by the prior dogfood run
(`2026-05-21-better-worktree-name-template`).

## Stage-numbering scheme

Map state name → directory name:

```
draft       -> 1_draft
shaping     -> 2_shaping
planning    -> 3_planning
building    -> 4_building
validating  -> 5_validating
followups   -> 6_followups
```

Applied to both `stages/` and `archive/`. `qa/` and `qa-v<N>/` keep their
existing names (already version-numbered). `human_review` has no
directory.

## Changes

### TODO #1: numbered stage directories

1. `agent-workbench-live/lib/lifecycle.py`
   - Add `_STAGE_NUMBER` map and `_stage_dirname(stage)` helper.
   - `stage_dir`, `archive_dir` route the stage name through `_stage_dirname`.
   - `_STAGE_OUTPUTS` `dest_stage` values stay as state names; the move
     code uses `_stage_dirname` to compute the on-disk dirname.
   - `archive_for_bounce` iterates state names → resolved via `stage_dir`.

2. `agent-workbench-live/lib/cli/cmd_start.py` — update seed-path strings.
3. `agent-workbench-live/lib/cli/cmd_validate.py` — update hint + path
   strings.
4. `agent-workbench-live/lib/cli/cmd_followups.py` — update
   `artifacts.followups` path string.
5. `agent-workbench-live/lib/followups.py` — update docstring.
6. `agent-workbench-live/.claude/commands/followups.md` — update doc
   paths.
7. `agent-workbench-live/templates/build.md` — update doc path.
8. `agent-workbench-live/templates/HUMAN_REVIEW.md` — update hub links.
9. `docs/lifecycle.md` — update ASCII tree + one-liner about in-flight
   runs.
10. `agent-workbench-live/tests/test_lifecycle.py`,
    `tests/test_integration.py`,
    `tests/test_transitions.py` — update string assertions.

### Follow-up A: scope_check path-prefix ambiguity

`lib/scope_check.detect_creep`: change `detect_creep` to treat an actual
path as expected if any expected path is a suffix of the actual path
(handling the workbench-relative vs. worktree-root-relative confusion).
Update `templates/brief.md` "Files likely to change" comment to note that
either workbench-relative or worktree-relative paths work. Add unit test.

### Follow-up B: unit tests for `extract_run_date`

New file `agent-workbench-live/tests/test_run_ids.py`. Covers: empty
string, missing date prefix, malformed date prefix, valid case, NamingError.

### Follow-up C: render `build:` block in `agent-workbench show`

`lib/cli/cmd_show.py`: read `meta.get("build")` and print the three
fields if present.

### Follow-up D: multi-line ASM/DR parser

`lib/cli/cmd_plan.py`: extend the `- **Field**: …` body capture to slurp
continuation lines (indented or non-empty, until next dash or `###`).
Tests added.

## Tests

### Unit

- `tests/test_lifecycle.py` — string updates + new
  `test_stage_dir_is_numbered`.
- `tests/test_scope_check.py` — new
  `test_detect_creep_handles_path_prefix_difference`.
- `tests/test_run_ids.py` — new file.
- `tests/test_cmd_plan_parser.py` (or extension in an existing test) —
  multi-line ASM/DR body capture.

### Integration

- `tests/test_integration.py` — replace `stages/<name>/` strings with
  `stages/<N>_<name>/`. The 93→? tests should pass.

### Manual

```
python3 -m unittest discover -s agent-workbench-live/tests
```
