---
description: Create a new Agent Workbench run from a raw idea. Use when the user wants to start a new run targeting a specific repo path with a worktree name and an idea text.
---

# /new-run

Thin wrapper around `agent-workbench new-run`. Creates a fresh run in state `draft`.

## What you need from the user

- `--repo-path <path>` (existing repo) OR `--new-repo-path <path>` (will be created with monorepo scaffold)
- `--worktree-name <slug>` — kebab-case, short
- The raw idea text (paste it, or point at a file via `--idea-file`)

## Run

```bash
agent-workbench new-run \
  --repo-path /Users/me/code/some-repo \
  --worktree-name add-login-form \
  --idea-file ./my-idea.md
```

If reading from stdin:

```bash
echo "Build a thing." | agent-workbench new-run --repo-path ... --worktree-name ...
```

The command prints the `run_id` on success. Save it; you'll pass it to every subsequent command.

## Next step

Run `/shape <run_id>` to start the LLM-bearing shaping pass.

## Reference

See `docs/lifecycle.md` § `draft` for the contract.
