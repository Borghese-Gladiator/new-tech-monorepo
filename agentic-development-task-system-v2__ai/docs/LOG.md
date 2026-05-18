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
