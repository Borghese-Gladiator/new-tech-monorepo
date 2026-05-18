# TODO

Next round of work after V1. Each section captures one idea — what it is, why we want it, and the concrete pieces to build.

---

## 1. Automatic E2E testing

V1 has unit tests + integration tests that drive the CLI through the happy path / bounce / abandon. What's missing is a true end-to-end smoke that exercises the full LLM-bearing flow (`/shape`, `/plan`, `/validate`) against a real throwaway repo without a human in the loop.

- [ ] Define what "E2E" means here: one fixture repo + one canned `raw-idea.md` driven from `new-run` to `complete` with no manual prompts.
- [ ] Pick the harness. Options: a `scripts/e2e.sh` shell driver, a `tests/test_e2e.py` that subprocesses the CLI + a stub LLM, or a real Claude Code headless invocation. Default: shell driver that calls the CLI; LLM steps stubbed by writing canned artifact files (`brief.md`, `plan.md`, `review.md`, `qa/report.md`).
- [ ] Build a `tests/fixtures/e2e/` tree: throwaway repo seed, `raw-idea.md`, canned outputs for each LLM-bearing stage.
- [ ] Wire a `--stub-llm` (or env var `AGENT_WORKBENCH_STUB_LLM=1`) mode so `/shape`, `/plan`, `/validate` skip the model and copy fixture artifacts into the run directory. Slash command bodies stay unchanged; the Bash prefix branches on the flag.
- [ ] Assertions per stage: state advanced correctly, expected artifacts exist, `events.jsonl` contains the expected event types in order, `audit.md` renders.
- [ ] Run the E2E in CI on every push to a feature branch. Fail loudly on any unexpected event or state.
- [ ] Add a second E2E that exercises the **bounce loop** (validate → bounce → validate → complete) and a third for **abandon** at a random non-terminal state.
- [ ] Document how to add a new E2E scenario in `agent-workbench-live/tests/README.md`.

## 2. Task board

Right now run state is scattered across `runs/<run_id>/metadata.yaml` files. To see what's in flight you have to `agent-workbench list` and squint. A task board surfaces all runs grouped by lifecycle state so humans can see queue depth and what needs attention.

- [ ] Decide format. Default: terminal-rendered Kanban (`agent-workbench board`) with one column per state (`draft`, `shaping`, `planning`, `ready`, `building`, `validating`, `human_review`, `done`, `abandoned`). Stretch: an HTML render written to `runs/_board.html` for browser viewing.
- [ ] Add `agent-workbench board` subcommand. Reads every `runs/*/metadata.yaml`, groups by status, prints columns with `run_id`, age (since `updated_at`), `repo_name`, branch.
- [ ] Highlight runs that have been in `human_review` for more than N hours (configurable in `agent-workbench.yaml.board.stale_human_review_hours`).
- [ ] Hide terminal states by default; `--all` includes `done` and `abandoned`.
- [ ] Slash command `/board` — thin wrapper.
- [ ] (Stretch) `agent-workbench board --html <path>` writes a single self-contained HTML file. No server, no JS framework — just a static dump regenerated on demand.
- [ ] (Stretch) Per-run "blocker" field in metadata so the board can show *why* a run is stalled in `human_review` (e.g., "waiting on QA env").

## 3. Activity log summary

`events.jsonl` is the source of truth but it's noisy — every `CommandRun` and `ArtifactWritten` is in there. We need a human-readable rollup that answers "what happened today across all runs?" without re-running `audit.md` for each run.

- [ ] Add `agent-workbench summary` subcommand. Default window: last 24 hours. Flags: `--since <ISO date>`, `--until <ISO date>`, `--run <run_id>` to scope to one run.
- [ ] Output sections: **Started** (new `RunCreated` events), **Advanced** (state transitions, one line each), **Completed** (`RunCompleted`), **Abandoned** (`RunAbandoned`), **Bounced** (`BounceRequested`), **Still in flight** (runs that had any event in window but no terminal outcome).
- [ ] Group by run, then by event-time. Collapse `CommandRun` / `ArtifactWritten` into counts instead of listing each.
- [ ] Markdown output by default; `--format json` for machine readers.
- [ ] Cron-friendly: `agent-workbench summary --since yesterday --format markdown > docs/LOG-auto-$(date +%F).md` should produce a clean daily log entry suitable for pasting into `LOG.md`.
- [ ] Slash command `/summary` — thin wrapper, defaults to last 24h, prints inline.
- [ ] Decision needed: do we *append* daily summaries to `LOG.md` automatically, or keep `LOG.md` hand-curated and let `summary` be a read-only tool? Default: hand-curated; `summary` is read-only.

## 4. Better worktree name

Today `worktree_name` defaults to the slug of the brief title — fine for short titles but loses information for longer ones, and there's no signal of *what stage* the work is in or *which repo* it targets when you're staring at a `worktrees/` directory.

- [ ] Audit current naming: `worktrees/<repo_name>/<slug>`. Document the failure modes (collisions when two runs share a slug; opaque names when slugs are truncated; no date hint).
- [ ] Decide on a new template. Candidate: `<YYYYMMDD>__<slug>` (matches the existing `LOCAL_worktrees` convention this repo uses — see `202605_agent_workbench_v2`). Alternative: `<run_id>` directly (already date-prefixed + slug, guaranteed unique).
- [ ] Update `agent-workbench.yaml.defaults.worktree_name_template` and the resolver in `lib/run_ids.py`.
- [ ] Decide whether `branch_name` follows the same pattern. Current: `agent/<worktree_name>`. Probably stays — but verify the new template doesn't break git's branch name rules.
- [ ] Migration story for existing in-flight runs: don't rename them. New template applies only to runs created after the change. Add a one-line note in `lifecycle.md`.
- [ ] Update integration tests that assert on worktree paths.
- [ ] Update `AGENTS.md` and `README.md` examples.
- [ ] (Stretch) Allow the user to override per-run via `new-run --worktree-name <name>` — already supported; just make sure the slug-sanitizer doesn't strip the new template's separators (`_`, double-underscore).
