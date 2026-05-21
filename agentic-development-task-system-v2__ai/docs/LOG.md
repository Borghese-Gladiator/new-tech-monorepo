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

## 2026-05-20

Completed all seven subsections of the Renovate task workflow (TODO §1) across four passes — every staged run now uses the new layout, the new gates, and the new lifecycle. Resulting on-disk reviewer experience: 5 top-level entries instead of 15; `HUMAN_REVIEW.md` with required "Suggested first checks" + "Run timeline" sections as the entry point.

- **Pass 1 (`d1d8b44`) — §1a/§1b/§1c:** new `lib/lifecycle.py` (layout detection, move-on-transition, bounce supersession with `-v<N>` versioning, empty-dir pruning, HUMAN_REVIEW.md section validator); transition engine rewrites evidence paths on staged runs; file mergers (`plan.md` folds Preflight + Decisions & assumptions; `build.md` merges implementation-summary + diff-summary); HUMAN_REVIEW.md replaces handoff.md. Back-compat: existing flat-layout runs (e.g. `runs/2026-05-18-poker/`) read-only forever, never migrated.
- **Pass 2 (`d5ee45e`) — §1d/§1e:** `metadata.yaml` gains a `build:` block with `iterations` / `exit_reason` / `max_iterations`; `building → validating` requires `build_iterations` + `build_exit_reason` evidence; new `lib/doc_claims.py` parses `build.md`'s "Documentation touched" section and shells out to `git diff --name-only` to flag false claims, appending findings to `review.md` and emitting `DocClaimsVerified`.
- **Pass 3 (`90a3daf`) — §1f:** new `followups` lifecycle stage between `validating` and `human_review`; new `lib/followups.py` parses + validates YAML frontmatter entries with the 5-category enum + `no_followups` sentinel; new `agent-workbench followups` CLI + `/followups` slash command author `stages/followups/follow-ups.md` (LLM-driven, no execution); HUMAN_REVIEW.md section gate moved from the old direct `validating → human_review` (still in schema for flat-layout legacy runs) to the new `followups → human_review`. Also fixed a pre-existing flaky integration test (worktree-path assertion that depended on tempdir-name slug round-tripping).
- **Pass 4 — §1g:** new `lib/scope_check.py` parses `brief.md`'s `## Files likely to change` (or `## Scope`) section and compares against `git diff --name-only <base>...HEAD`; unexpected files appended to `review.md` as `## Scope creep check`; emits `ScopeCreepChecked` event. Deep blast-radius (depth-2/3 caller traversal) is authored by the reviewer agent itself via `git` commands during `/validate` step 3 — the CLI handles the deterministic depth-1 comparison only. Fixed a bullet-regex bug (greedy/non-greedy interaction) that affected both `lib/doc_claims.py` and the new `lib/scope_check.py`.

End state: 93 tests across 8 test modules; `agent-workbench doctor` passes; the flat-layout poker run still loads. TODO file renumbered — §1 is now "Better worktree name"; §6 added: "Followup spawn" (the deferred stretch from §1f).

## 2026-05-21

First end-to-end dogfood of the staged-layout workflow. Drove TODO §1 (Better worktree name) through the full pipeline on this repo itself.

- Run `2026-05-21-better-worktree-name-template` traversed all 8 transitions (`draft → shaping → planning → ready → building → validating → followups → human_review → done`) without any manual intervention beyond authoring the LLM-bearing artifacts. The new staged layout, doc-claims check, build-loop metadata fill, scope-creep check, and `/followups` stage all fired correctly.
- Real work landed: `agent-workbench-live/lib/run_ids.py` gained `extract_run_date` + a widened `make_worktree_path` that prepends `<YYYYMMDD>__` to worktree directory basenames. Branch `agent/better-worktree-name-template` (commit `cefd720`) merged into `202605_agent_workbench_v2`; dogfood worktree removed.
- Dogfood surfaced four follow-up items, captured in `runs/2026-05-21-better-worktree-name-template/stages/followups/follow-ups.md`. Top item — numbered stage directories — promoted to TODO §1 because the alphabetical sort of `stages/<stage>/` (`building/ draft/ followups/ planning/ shaping/ validating/`) is actively confusing at triage time.
- Confirmed by inspection: this run's *own* worktree did NOT get the date prefix (the implementation landed mid-run, AC-4 preservation). Future runs will.
