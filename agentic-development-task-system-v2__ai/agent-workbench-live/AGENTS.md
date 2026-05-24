# AGENTS.md

You are an AI agent (Claude Code, Codex, Cursor, anything similar) that has opened the Agent Workbench. This file tells you how to operate here.

If something below is unclear, read `../architecture.md` and `../docs/lifecycle.md` for the full design. This file is the short version.

---

## What this is

Agent Workbench is a local run orchestrator. One run = one fuzzy idea turned into one isolated git worktree, one feature branch, one set of artifacts, and one audit trail. It does not embed an agent. **You** are the agent. The workbench is the substrate.

## The lifecycle (memorize this)

```text
draft -> shaping -> planning -> ready -> building -> validating -> human_review -> done
```

Any non-terminal state can also go to `abandoned`. `human_review` can bounce back to `building`.

| State | What happens | You may ask questions? | You may read code? |
|---|---|---|---|
| `draft` | Raw idea captured. | **Yes** | No |
| `shaping` | Write `brief.md` from raw idea. | No | No |
| `planning` | Inspect repo, write plan + assumptions + decisions + preflight. | No | Yes |
| `ready` | Human approval gate. | N/A | N/A |
| `building` | Implement inside the worktree. | No, unless hard-blocked | Yes |
| `validating` | Self-review + QA + render audit + handoff. | No | Yes |
| `human_review` | Branch is ready for the human. | Human decides | Yes |
| `done` | Accepted. Terminal. | No | No |
| `abandoned` | Stopped intentionally. Terminal. | No | No |

## Two hard rules

1. **Only `draft` may ask the human clarifying questions.** Every other state must proceed by recording an assumption (`assumptions.md`), making a decision (`decisions.md`), or stopping with evidence.

2. **Only `lib/transitions.transition(...)` writes `status`.** Never edit `runs/<run_id>/metadata.yaml`'s `status` field directly. Never append to `events.jsonl` by hand. Use the CLI; the CLI calls the transition engine; the engine emits the right events.

## How to drive the workbench

Run the CLI:

```bash
agent-workbench <subcommand> [args]
```

Or invoke the matching slash command if you're in a Claude Code session (slash commands wrap the CLI for the LLM-bearing steps).

### Command -> state map

| Command | Transition | When to use |
|---|---|---|
| `new-run` | (creates run in `draft`) | A new idea arrives. |
| `shape <id>` | `draft -> shaping -> planning` | LLM-bearing. Use `/shape`. |
| `plan <id>` | `shaping -> planning -> ready` | LLM-bearing. Use `/plan`. |
| `start <id>` | `ready -> building` | Human approved; create branch + worktree. |
| `validate <id>` | `building -> validating -> human_review` | LLM-bearing. Use `/validate`. |
| `handoff <id>` | (read-only) | Re-display handoff info. |
| `complete <id>` | `human_review -> done` | Human accepted. |
| `bounce <id>` | `human_review -> building` | Human wants changes. |
| `abandon <id>` | any non-terminal -> `abandoned` | Stop the run. |
| `list` / `show` / `events` | (read-only) | Inspect state. |

### Slash commands

LLM-bearing (you read+write artifacts inside these):

- `/shape` — write `brief.md` from `raw-idea.md`.
- `/plan` — inspect the target repo, write `plan.md`, `preflight.md`, `assumptions.md`, `decisions.md`.
- `/validate` — review + QA + render `audit.md` and `handoff.md`.

Thin wrappers (just call the CLI):

- `/new-run`, `/start`, `/handoff`, `/complete`, `/bounce`, `/abandon`, `/runs`, `/run-show`.

## Source of truth

- `runs/<run_id>/metadata.yaml` — current state, pointers to artifacts. Written only by the metadata + transitions modules.
- `runs/<run_id>/events.jsonl` — append-only history. Written only by the events module.
- `runs/<run_id>/*.md` — the artifacts you fill in (brief, plan, assumptions, decisions, implementation-summary, etc).
- `runs/<run_id>/audit.md` — human-readable timeline, rendered from `events.jsonl` + artifacts during validation.

Directory names, branch names, and worktree paths are **not** sources of truth. If they disagree with `metadata.yaml`, `metadata.yaml` wins.

## When you get stuck

- **Ambiguity during `shaping` or `planning`** → record an assumption in `assumptions.md` and continue with the safest small implementation. Do not ask the human.
- **A command failed during `building`** → record what happened in `implementation-summary.md`. Try to repair. Do not silently retry. If you cannot proceed, hand off with known issues; the human can bounce or abandon.
- **State seems wrong** → run `agent-workbench show <run_id>` and `agent-workbench events <run_id>`. Never patch `metadata.yaml` to "fix" state.
- **A transition is rejected** → read the `TransitionRejected` event's `reason` field. The missing evidence is listed there.

## Subagent discipline

When you fan out work via Claude Code's Agent tool:

- The master session owns lifecycle state. Subagents return findings; the master decides whether to advance status.
- Pick the narrowest agent type. `Explore` for read-only search. `Plan` for planning. `general-purpose` only when edits or tool use are needed.
- Subagents are session-internal. They never write `metadata.yaml` or `events.jsonl`.

## Context library

Conventions, safety defaults, and per-language quartets live under `context/`. Agents lazy-import individual files via `@context/path/to/file.md` on demand — pull in the leaf you need at the moment you need it.

Start at `@context/README.md` — it indexes every file with one-line descriptions and import paths. Do not enumerate the library here; the index is the single source of truth and stays in sync as files are added or removed.

Adding or editing a leaf? Read `@context/AUTHORING.md` first.

## Where to read more

- `../architecture.md` — why it's shaped this way.
- `../docs/lifecycle.md` — every stage's contract (inputs, produces, exit evidence).
- `../docs/LOG.md` — chronological log of project decisions.
- `schemas/transitions.yaml`, `schemas/run-metadata.yaml`, `schemas/events.jsonl` — the formal contracts the CLI enforces.

## Regeneration

This file should be updated when:

- A CLI command is added, renamed, or removed.
- The lifecycle changes (new state, dropped state, new transition).
- Either hard rule above changes.
