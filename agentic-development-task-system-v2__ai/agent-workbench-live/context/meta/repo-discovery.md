# Repo discovery

Applies when: opening an unfamiliar repo — about to pick a test runner, lint command, or CI invocation.

Do:

- Run `pwd` first; confirm you're where you think you are.
- Detect language and package manager by manifest, not by reading code.
- Prefer repo-local scripts (`bin/test`, `Makefile`, `package.json` scripts) over invoking tools directly.
- Read `AGENTS.md` and `CLAUDE.md` at the repo root before any other doc; they encode local overrides.
- Use the same lint / typecheck / test command CI uses. Mismatched commands hide failures.
- Treat a `Makefile` target as authoritative if it exists for the operation you want.

Do not:

- Do not assume Poetry / Yarn / Make just because they're popular. Check the manifest.
- Do not bypass repo-local scripts to call the underlying tool directly unless the script is broken.
- Do not run `npm install` or `pip install` in a Yarn / Poetry repo.

Commands:

```bash
pwd
ls
find . -maxdepth 3 \( -name pyproject.toml -o -name package.json -o -name go.mod -o -name Cargo.toml \) -not -path '*/node_modules/*'
find . -maxdepth 3 \( -name AGENTS.md -o -name CLAUDE.md -o -name Makefile \) -not -path '*/node_modules/*'
# CI config — pick one, mirror it locally
ls .github/workflows/ .buildkite/ .circleci/ 2>/dev/null
```
