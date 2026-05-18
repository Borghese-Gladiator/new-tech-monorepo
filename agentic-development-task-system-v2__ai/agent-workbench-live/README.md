# agent-workbench-live

The working implementation of Agent Workbench.

The design lives one level up (`../architecture.md`, `../docs/lifecycle.md`, `../schemas/`). This folder is the running system.

## Layout

```text
agent-workbench-live/
  AGENTS.md              # how an AI agent should operate here
  agent-workbench.yaml   # workbench config (paths, defaults, policies, gates)
  bin/
    agent-workbench      # CLI entrypoint
  lib/                   # Python modules (stdlib only)
    config.py            # workbench config loader
    metadata.py          # runs/<run_id>/metadata.yaml read/write
    events.py            # append-only event log
    transitions.py       # the state machine
    locks.py             # per-run filesystem lock
    repos.py             # git + worktree manager
    audit.py             # render audit.md
    run_ids.py           # run_id / slug / branch / worktree naming
    yaml_io.py           # stdlib YAML reader/writer (flat subset)
  schemas/               # runtime copies of ../schemas
  templates/             # stub markdown for each artifact
  .claude/commands/      # slash commands
  scripts/               # deterministic bash glue
  tests/                 # unit + integration tests
  runs/                  # one dir per run (created lazily)
  worktrees/             # one dir per repo per worktree (created lazily)
```

## Quickstart

```bash
# from this directory
export PATH="$PWD/bin:$PATH"

agent-workbench new-run \
  --repo-path /Users/me/code/some-repo \
  --worktree-name add-login-form \
  --idea-file ./my-idea.md
```

Use `/shape`, `/plan`, `/validate` from a Claude Code session for the LLM-bearing steps. Use `agent-workbench start`, `complete`, `bounce`, `abandon` directly.

## Implementation status

See `../docs/TODO.md` for the full implementation plan. Sections checked off in order.
