# Plan — TODO §2: Live board card attributes

## Brief

Surface twelve already-on-disk fields on the live-board card so a reviewer
can triage from the board without opening the run dir. Land each as an
additive frozen attribute on `RunSnapshot` (lib/board/source.py) with a
unit test, then expose it in the Textual renderer (lib/board/app.py) and
the `--static` fallback (lib/cli/cmd_board.py).

The §3 layout polish (bands, rules, colour grading) is *not* in scope —
this pass only adds the data + the simplest renderer change that surfaces
it. §3 will restructure how it's displayed.

## Changes

### lib/board/source.py

Add to `RunSnapshot`:

- `scope_kind: str` — `meta.scope.kind`.
- `is_live: bool` — any `recent_events[0].age_seconds <= 60`.
- `ac_total: int | None`, `ac_covered: int | None` — parsed from the
  `## Acceptance criteria coverage` table in `stages/4_building/build.md`.
  None if section missing.
- `ac_table_missing: bool` — build.md exists but no AC section.
- `diff_added: int | None`, `diff_removed: int | None`,
  `diff_files: int | None` — `git diff --shortstat <base_ref>...HEAD` run
  against the worktree, lazy + TTL-cached on `(run_id, updated_at)`.
- `avg_iteration_seconds: float | None` — derived from gaps between
  successive `TransitionApplied` *into* `building`.
- `bounced_from: str | None`, `bounced_at_age_seconds: float | None` —
  populated when the most recent `TransitionApplied` is `human_review ->
  building`. Distinct from `recent_bounce_reason`, which tracks the most
  recent `BounceRequested` payload.
- `followups_categories: tuple[tuple[str, int], ...]` — counts per
  category, derived from the most recent `FollowupsRecorded` payload's
  `categories` list.
- `repo_path_tail: str` — last 2 path segments of `target.repo.path`.
- `worktree_missing: bool` — `target.worktree.created == False` AND
  status is `building` or later.
- `tests_recorded_age_seconds: float | None` — age of most recent
  `QACompleted` event.
- `completed_at: str | None`, `accepted_by: str | None`,
  `abandoned_reason: str | None` — direct passthrough from
  `meta.completion`.

The git-diff cache lives in source.py at module level: dict keyed by
`(run_id, updated_at)`. Cache eviction = unbounded across a board
session; that's fine — tens of runs, each entry tiny.

### lib/board/app.py

Status-aware additions in `_status_body` + supporting text fragments in
the title line:

- Title line: append `  [<status>]` (badge) and `<scope_kind>` to the
  right of the run_id.
- Title line gets a `● live` suffix when `run.is_live`.
- Title line gets `repo · <repo_path_tail>` underneath repo line when
  `repo_path_tail` differs from `repo_name`.
- `building` body: add `↩ bounced from <from> · <age>` when `bounced_from`
  set; add `avg <N>m/iter` when `avg_iteration_seconds` present; add
  `+A/-R across F files` diff line when diff present.
- `validating` body: replace `tests <mark>` with `tests <mark> · <age> ago`
  when `tests_recorded_age_seconds` present. Add `<C>/<T> ACs covered`
  (or `AC table missing` soft flag). Add the same diff line.
- `followups`/`human_review` body: append per-category breakdown when
  `followups_categories` non-empty.
- Soft warning line `! worktree missing` when `worktree_missing`.
- Terminal cards (`done`/`abandoned`) under `--all`: append
  `accepted_by <name> · <HH:MM>` or `abandoned: <reason>`.

### lib/cli/cmd_board.py

The `--static` text path currently renders a 4-line card. Promote it to
mirror the new info: leave the per-line API but extend it to include a
status-aware data line and a flags line. Add light support so the static
output shows the bounce / diff / AC counts when present — same source
field for both renderers, so the tests cover both.

### tests/test_board_snapshot.py

One test per new field, mostly small additions:

- `test_scope_kind`
- `test_is_live_when_recent_event`
- `test_ac_coverage_parsed`
- `test_ac_table_missing_flag`
- `test_avg_iteration_seconds`
- `test_bounced_from_on_recent_transition`
- `test_followups_categories_counts`
- `test_repo_path_tail`
- `test_worktree_missing_flag`
- `test_tests_recorded_age_seconds`
- `test_completion_fields_passthrough`

Git diff: skip the cache-key-aware test in unit tests; the cache + shell
behaviour is exercised by a single lazy test that monkeypatches
`subprocess.run` and asserts the cache hit on the second call.

## Tests

### Unit

`bin/pytest -m unit agent-workbench-live/tests/test_board_snapshot.py`

### Manual

- Static fallback against the existing `runs/`:
  ```
  cd agent-workbench-live
  python agent-workbench board --static --all
  ```
  Eyeball:
  - The Shogi run shows `[done]`, scope `bootstrap`, `accepted_by tim`.
  - The Poker run is loud + shows `bounces:` if it had any.
- Live TUI smoke (deps required):
  ```
  pip install -r agent-workbench-live/requirements-board.txt
  python agent-workbench-live/agent-workbench board --all
  ```
  Inspect a building / validating / followups card visually. Quit with q.
