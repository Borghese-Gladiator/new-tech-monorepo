# Plan — Task board (TODO §1)

## Brief

Add `agent-workbench board`, a terminal-rendered Kanban over `runs/<run_id>/metadata.yaml`. One column per lifecycle state. Each card carries `run_id`, age since `updated_at`, `repo_name`, branch. Terminal states (`done`, `abandoned`) hidden by default; `--all` includes them. Runs in `human_review` longer than a configurable threshold are flagged stale. Wire `/board` as a thin slash wrapper.

Out of scope (TODO §1 explicit Stretch — deferred):
- `--html` static dump.
- Per-run `blocker` metadata field.

## Changes

1. **`agent-workbench-live/agent-workbench.yaml`** — add `board.stale_human_review_hours: 24`.
2. **`agent-workbench-live/lib/cli/cmd_board.py`** — new subcommand.
   - Loads each run via `metadata.load(cfg, run_id)`; skips unreadable runs without aborting.
   - Groups by `status` in canonical lifecycle order: `draft, shaping, planning, ready, building, validating, followups, human_review, done, abandoned`.
   - Hides `done` + `abandoned` columns unless `--all`.
   - Filters to a single status when `--status X` is passed.
   - Columns rendered side-by-side using fixed-width formatting (no curses; plain stdout — same model as `cmd_list_runs`).
   - Card lines (3 lines per card + blank separator):
     - `<run_id>`
     - `<age> · <repo_name>`
     - `<branch>`
   - Age computed from `metadata.updated_at`, displayed as `Nm`, `Nh`, or `Nd` (largest unit ≥ 1, integer; `<1m` shown as `0m`).
   - Stale: if `status == "human_review"` and age ≥ `board.stale_human_review_hours`, prepend `!` to the run_id line and surface in a "Stale" footer.
   - Empty board prints `(no runs)`.
3. **`agent-workbench-live/bin/agent-workbench`** — append `"board"` to `SUBCOMMANDS`.
4. **`agent-workbench-live/.claude/commands/board.md`** — thin slash wrapper.
5. **`agent-workbench-live/tests/test_cmd_board.py`** — new test module.

## Tests

### Unit

`tests/test_cmd_board.py` builds a tmp workbench, seeds fake `runs/<id>/metadata.yaml` files at various statuses (draft, building, fresh human_review, stale human_review, done), then invokes the CLI via subprocess (same pattern as `tests/test_integration.py`). Assertions:

- Columns appear in canonical order.
- Each non-empty column contains the run_id of the seeded run.
- Stale human_review run is prefixed with `!` and listed in the Stale footer.
- `done` column hidden by default; visible with `--all`.
- `--status building` shows only the building column.
- Empty workbench prints `(no runs)`.
- Age formatter (invoked directly on the module): 0s → `0m`, 90s → `1m`, 7200s → `2h`, 90000s → `1d`.

### Manual

- `agent-workbench board` against this repo's real `runs/` (one `done`, one `human_review` — verify the human_review run is flagged stale since it's > 24h old).
- `agent-workbench board --all` — adds the `done` column.
- `agent-workbench board --status human_review` — only that column.
