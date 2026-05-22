# Risk and approval

Applies when: about to take any action whose blast radius extends beyond the local working tree.

Do:

- Classify the action before running it:
  - **Low** — local file edits, reads, running tests, scoped commits on a feature branch.
  - **Medium** — committing, opening a draft PR, installing dependencies, modifying CI config.
  - **High** — force-push, destructive deletes (`rm -rf`, `git branch -D`, `git reset --hard`), destructive migrations, sending messages to humans, publishing artifacts.
- Prefer reversible operations. A two-commit fix beats `--amend`.
- For medium actions, state what you're about to do, then proceed.
- For high actions, **stop and ask** unless the user has explicitly pre-authorized.
- Pre-authorization is scope-bounded: "go ahead and push" authorizes this push, not all future pushes.

Do not:

- Do not force-push to `main` / `master` ever. Refuse and surface the request.
- Do not skip hooks (`--no-verify`, `--no-gpg-sign`) without explicit approval.
- Do not run `rm -rf`, drop tables, or delete branches as a shortcut around an obstacle.
- Do not infer "the user wants this" from absence of objection. Silence is not consent.

Commands:

```bash
# Before a high-risk action, audit what's about to change.
git status --short
git branch --show-current
git log --oneline -5
```
