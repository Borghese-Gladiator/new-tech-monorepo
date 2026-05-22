# CLAUDE.md

Project-specific guidance for Claude Code sessions opened against this repo. Read alongside `~/.claude/CLAUDE.md` (user-global) and `AGENTS.md` (which governs the two-file LOG/TODO contract for infrastructure work).

## Context library

Conventions, safety defaults, and per-language quartets live under `agent-workbench-live/context/`. Use Claude Code's lazy `@context/...` import to pull in only the file you need at the moment you need it — do not load the whole tree.

- Start here: `@context/README.md` — indexes every file with one-line descriptions and import paths.
- Almost always relevant: `@context/meta/repo-discovery.md` and `@context/meta/risk-and-approval.md`.

Prefer focused imports. Each context file is one screen and follows the same four-marker template (`Applies when:` / `Do:` / `Do not:` / `Commands:`). Pull in `@context/git/commit.md` when you're about to commit; pull in `@context/languages/python/testing.md` when you're about to write a Python test. Do not preload everything.

## Slash commands

Project slash commands live under `agent-workbench-live/.claude/commands/`. They wrap the `agent-workbench` CLI for the LLM-bearing lifecycle stages (`/shape`, `/plan`, `/validate`, `/followups`) and the thin transitions (`/new-run`, `/start`, `/bounce`, `/complete`, `/abandon`). Commands do not pre-declare context imports — pull `@context/...` leaves as you need them.

## Where to read more

- `AGENTS.md` (repo root) — the two-file LOG/TODO contract for workbench-itself work.
- `agent-workbench-live/AGENTS.md` — in-run lifecycle discipline (only `draft` asks questions; only `lib/transitions.transition` writes status).
- `docs/lifecycle.md` — every stage's contract.
- `docs/architecture.md` — why the workbench is shaped this way.
