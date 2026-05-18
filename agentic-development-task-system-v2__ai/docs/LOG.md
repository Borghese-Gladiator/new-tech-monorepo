# LOG

Chronological log of what happened on this project.

---

## 2026-04

- First attempt. Built something overly convoluted that did not match my existing workflow. Shelved.

## 2026-05 (early)

- Second attempt. Simple in concept, but combined too many conflicting ideas (e.g., beads vs. SQLite task database). Shelved.

## 2026-05-17

- Started the third attempt — branch `202605_agent_workbench_v2`.
- Goal: focus on the MVP, not a general agent platform.
- Drafted `docs/architecture.md` and `docs/lifecycle.md` as a thinking pass.
- Completed V1 of agent-workbench end-to-end (moved out of `TODO.md`):
  - **Repo bootstrap:** Python 3 (stdlib only); project skeleton under `agent-workbench-live/` (`AGENTS.md`, `bin/agent-workbench`, `lib/`, `.claude/commands/`, `scripts/`, `runs/`, `worktrees/`, `tests/`); dispatcher wired; workbench root resolved via env/default; `AGENTS.md` written with lifecycle + invariants.
  - **Core libraries:** `lib/metadata.py` (load/save/create/validate), `lib/events.py` (append-only, schema-validated), `lib/transitions.py` (transition engine, evidence checks, secondary events, wildcard `*->abandoned`), `lib/locks.py` (per-run lock), `lib/repos.py` (verify_existing / create_new / create_worktree / remove_worktree, repo-name disambiguation, `git -C`), `lib/run_ids.py` (slugged IDs + name templates), `lib/audit.py` (render `audit.md`, idempotent), `lib/config.py` (typed config accessors).
  - **CLI commands:** `new-run`, `shape`, `plan`, `start`, `validate`, `handoff`, `complete`, `bounce`, `abandon`, plus read-only `list` / `show` / `events`.
  - **Slash commands:** all thin wrappers (`/new-run`, `/start`, `/handoff`, `/complete`, `/bounce`, `/abandon`, `/runs`, `/run-show`) and LLM-bearing (`/shape`, `/plan`, `/validate`) under `agent-workbench-live/.claude/commands/`.
  - **Templates:** `raw-idea.md`, `brief.md`, `plan.md`, `preflight.md`, `assumptions.md`, `decisions.md`, `implementation-summary.md`, `diff-summary.md`, `review.md`, `qa/report.md`, `handoff.md`, `audit.md`.
  - **Tests:** unit tests for `metadata`, `events`, `transitions`, `yaml_io`; integration tests covering happy path, bounce loop, abandon, new-repo flow.
  - **Schema validation:** startup validates `schemas/events.jsonl`, `schemas/transitions.yaml`, `schemas/run-metadata.yaml`; `agent-workbench doctor` rechecks + verifies layout.
  - **Docs polish:** QUICKSTART merged into `README.md` (commit `febae6f`). Auto-generated `commands.md` deferred — not yet built.
  - **Out of scope for V1 (intentionally not built):** PR/merge automation, multi-repo runs, `project_subpath` / global repo registry, long-running daemon / job queue, web UI.

## 2026-05-18

- Created `agent-workbench-final/` as the canonical output folder.
- Wrote `README.md`, `architecture.md`, `lifecycle.md`, `agent-workbench.yaml`.
- Wrote schemas: `schemas/transitions.yaml`, `schemas/run-metadata.yaml`, `schemas/events.jsonl`.
- Fixed CLI command name: `complete` (not `accept`) for the `human_review -> done` transition. `accepted_by` stays as a metadata field; the command that records it is `complete`.
- Merged the rationale sections from `docs/architecture.md` into `agent-workbench-final/architecture.md` — centralized orchestration, worktree isolation, metadata canonicality, Python helpers, slash commands, subagent discipline, boundaries.
- Expanded `lifecycle.md` so each stage has an explicit contract (inputs, produces, rules, exit evidence).
- **Decision:** dropped the `project_subpath` concept and the global repo registry from V1. A run targets one repo path. The repo IS the project. Reconsider if a real monorepo-with-multiple-projects use case shows up.
- Deleted `docs/` after merging its content into `agent-workbench-final/`.
- Wrote `TODO.md` to track the next concrete piece of work: CLI command contracts for `new-run`, `shape`, `plan`, `start`, `validate`, `handoff`, `complete`, `bounce`, `abandon`.
