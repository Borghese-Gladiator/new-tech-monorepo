# gas_town_mayor_first__ai
Setup notes for [Gas Town](https://github.com/gastownhall/gastown) — Steve Yegge's multi-agent orchestration framework — together with [Beads](https://github.com/steveyegge/beads) for task tracking and [Dolt](https://github.com/dolthub/dolt) for versioned memory storage.

This repo hosts the Gas Town "mayor" installation (the central controller). Individual projects that the mayor orchestrates are called **rigs** and live in their own repos.

## Prerequisites
- **Go** — required to build Gas Town and Beads from source
- **Homebrew** — for installing Dolt (and `icu4c` if Beads build fails)
- **macOS** — these notes target macOS; adjust paths for other platforms

Ensure Go's bin directory is on your `PATH`:
```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export PATH="$PATH:$HOME/go/bin"  # golang
export PATH="$HOME/bin:$PATH"     # local binaries (gt, bd)
```

## Install Gas Town
Build from source — **do not** use `go install` on macOS (see note below).

```bash
git clone https://github.com/gastownhall/gastown.git
cd gastown
make build

mkdir -p ~/bin
cp ./gt ~/bin/gt
chmod +x ~/bin/gt
```

<details>
<summary>Why not <code>go install</code> on macOS?</summary>

Running `go install github.com/steveyegge/gastown/cmd/gt@latest` produces an unsigned binary that macOS will SIGKILL:
```
ERROR: This binary was built with 'go build' directly.
       macOS will SIGKILL unsigned binaries. Use 'make build' instead.
```

`make build` is the supported path on macOS.
</details>

## Install Beads
```bash
git clone https://github.com/steveyegge/beads
cd beads
make build

mv bd ~/bin/bd
```

<details>
<summary>Why build from source instead of <code>brew</code> / <code>go install</code>?</summary>

I initially tried each of the following and hit macOS-signing, build, or version issues:

- `brew install beads`
- `go install github.com/steveyegge/beads/cmd/bd@latest`
- `go install github.com/steveyegge/gastown/cmd/gt@latest`

One of the failures along the `go install` path was a CGO/ICU build error:

```
# github.com/dolthub/go-icu-regex/internal/icu
./file.h:1:10: fatal error: 'unicode/regex.h' file not found
    1 | #include "unicode/regex.h"
      |          ^~~~~~~~~~~~~~~~~
```

That one is fixable by installing ICU and pointing CGO at it:

```bash
brew install icu4c
export CGO_CFLAGS="-I$(brew --prefix icu4c)/include"
export CGO_LDFLAGS="-L$(brew --prefix icu4c)/lib"
```

…but between that, the macOS signing issue, and other version mismatches, building from source with `make build` turned out to be the most reliable path — so the ICU workaround above isn't needed on the documented path.
</details>

## Install Dolt
```bash
brew install dolt
```

## Verify the install
```bash
source ~/.zshrc
bd version
gt version
dolt version
```

## Set up this mayor repo
Run from any root
```bash
gt install /Users/timothy.shee/GitHub/new-tech-monorepo/gas_town_mayor_first__ai
gt init        # IF you want to initialize inside a git repo
# gt git-init  # IF you want gas_town to turn your current directory into a git re
```

If something looks off, Gas Town ships a self-repair command:
```bash
gt doctor --fix
```

## Start Dolt and initialize memory
The mayor uses Dolt as the versioned memory store. Start the Dolt server and initialize memory for your first rig:
```bash
gt dolt start
```

To start all Gas Town services at once:
```bash
gt up
```

## Register a rig
Rigs are individual projects that the mayor orchestrates. Each rig is its **own git repo** at an absolute path. Therefore, you CANNOT add it as a subdirectory inside the existing git repo. (kind of an annoying constraint for this monorepo, but sure separate out `git repos`)

create git repo (separate)
```bash
mkdir -p ~/GitHub/poker_web__ai
cd ~/GitHub/poker_web__ai
git init
git commit --allow-empty -m "Initial commit"
```

add as rig
```bash
gt rig add poker_web__ai file:///Users/timothy.shee/GitHub/poker_web__ai
```
- **Naming:** rig names may use underscores but **not hyphens** (`poker_web` ✅, `poker-web` ❌).

start a rig
```
gt rig start poker_web__ai
```

begin implementation
```
cd ~/GitHub/poker_web__ai
claude
```
> NOTE: Gas Town simply directs implementation in multiple directories. For example, I want to implement in poker_web_backend__ai AND poker_web_frontend__ai with communication. It does not inherently make implement poker_web_backend__ai faster.

Gas City is the more general follow up version (and less opinionated)


## Notes & gotchas
- Gas Town is **opinionated about git**: every rig must be its own repo, so you'll initialize and manage each rig's git state independently. `gt rig add` is supposed to handle this but doesn't always.
- Commands leave behind artifacts (e.g. `gt dolt init-rig <name>` creates a directory in the current repo). Run them from a deliberate working directory.
- Keep `gt doctor --fix` in mind when state drifts.
- You cannot just `rm -rf` to delete a project. There's a lot random folders that hold references to anything you create.

## What Gas Town changed in `~/.claude/settings.json` (and what I removed)

Installing Gas Town added two **global** Claude Code hooks that automatically committed dirty working trees as `WIP: checkpoint (auto)` after **every tool call** in **every Claude Code session, in every repo on the machine** — not just Gas Town worktrees. The hooks invoked `/Users/timothy.shee/.git-ai/bin/git-ai checkpoint claude --hook-input stdin`.

I was only experimenting with Gas Town and did not want auto-committing across all my repos, so I removed both entries. Backup of the original settings is at `~/.claude/settings.json.bak.pre-git-ai-removal`.

The two hook entries removed from `~/.claude/settings.json`:

```jsonc
// PostToolUse — fired after every tool use
{
  "matcher": "*",
  "hooks": [
    {
      "type": "command",
      "command": "/Users/timothy.shee/.git-ai/bin/git-ai checkpoint claude --hook-input stdin"
    }
  ]
}

// PreToolUse — fired before every tool use
{
  "matcher": "*",
  "hooks": [
    {
      "type": "command",
      "command": "/Users/timothy.shee/.git-ai/bin/git-ai checkpoint claude --hook-input stdin"
    }
  ]
}
```

The `git-ai` binary itself (`~/.git-ai/`) was left in place — only the Claude Code hook wiring was removed. To re-enable, restore the entries above (or `cp ~/.claude/settings.json.bak.pre-git-ai-removal ~/.claude/settings.json`).
