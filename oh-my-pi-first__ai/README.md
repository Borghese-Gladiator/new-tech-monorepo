# Oh My Pi — Setup (macOS)

[Oh My Pi](https://github.com/can1357/oh-my-pi) (`omp`) is a terminal AI coding agent — fork of `badlogic/pi-mono`. TypeScript/Bun + Rust native engine. Supports Anthropic / OpenAI / Gemini / Mistral / Groq / **Ollama** and many others, plus MCP servers, LSP integration, custom slash commands, and TUI sessions.

This folder is a setup playbook for installing `omp` on this machine (Apple M2 Max, 64 GB, macOS 26.4) and pointing it at the local **Ollama** stack we already have running for the `ollama-pi-coding-agent-first__ai` experiment.

---

## Prereqs

Already on this machine (verified):
- macOS 26.4, arm64
- Ollama (`/opt/homebrew/bin/ollama`) with models: `qwen3-coder:30b`, `qwen3-coder-next:latest`, `embeddinggemma:latest`, `llama3.1:latest`, `mistral:latest`, etc.

Missing (need to install):
- **Bun >= 1.3.7** — `omp` runs on Bun.

Optional but recommended:
- A terminal that supports the Kitty keyboard protocol. iTerm2 and Kitty work out of the box. Ghostty and wezterm need a one-line config tweak (see below).

---

## Install steps

### 1. Install Bun

```bash
curl -fsSL https://bun.sh/install | bash
```

Reload your shell, then verify:
```bash
bun --version   # must be >= 1.3.7
```

### 2. Install omp

Two options; pick one.

**A) Via Bun (recommended by upstream):**
```bash
bun install -g @oh-my-pi/pi-coding-agent
```

**B) Via installer script:**
```bash
curl -fsSL https://raw.githubusercontent.com/can1357/oh-my-pi/main/scripts/install.sh | sh
```

Verify:
```bash
omp --version
```

### 3. Terminal setup (only if needed)

iTerm2 / Kitty: nothing to do.

Ghostty (`~/.config/ghostty/config`):
```
keybind = alt+backspace=text:\x1b\x7f
keybind = shift+enter=text:\n
```

wezterm (`~/.wezterm.lua`):
```lua
local wezterm = require 'wezterm'
local config = wezterm.config_builder()
config.enable_kitty_keyboard = true
return config
```

### 4. Point omp at local Ollama

`omp` has a native Ollama provider — no OpenAI-compat shim needed.

Make sure Ollama is running (separate tab):
```bash
ollama serve
```

Then in your shell rc (`~/.zshrc`):
```bash
export OLLAMA_HOST=http://localhost:11434     # default — only set if non-default
# export OLLAMA_API_KEY=...                   # only if you've put auth in front of Ollama
```

### 5. (Optional) API keys for cloud models

If you want to mix in Anthropic / OpenAI / Gemini / Groq alongside Ollama:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...
export GROQ_API_KEY=...
```

`omp` round-robins across multiple credentials if you set them.

### 6. First run

```bash
cd ~/GitHub/new-tech-monorepo
omp
```

Inside the TUI:
- `/model` — pick a default model. For local, choose an `ollama/<name>` entry like `ollama/qwen3-coder:30b`.
- `?` — show keyboard shortcuts.
- `/extensions` — toggle which providers (Claude Code, Cursor, etc.) `omp` should auto-discover config from.

### 7. Setting role-based model defaults

> **Gotcha:** `omp config set` does not accept dotted record keys (e.g. `modelRoles.default` returns "Unknown setting"). Role assignment must happen via flags, env vars, or the TUI's `/model` selector.

Pick one of:

**A) Env vars (most durable — add to `~/.zshrc`):**
```bash
export PI_DEFAULT_MODEL=ollama/qwen3-coder:30b
export PI_SMOL_MODEL=ollama/llama3.1:latest
export PI_PLAN_MODEL=ollama/qwen3-coder:30b
```

**B) Per-invocation flags:**
```bash
omp --model ollama/qwen3-coder:30b --smol ollama/llama3.1:latest
```

**C) Interactively inside the TUI:** `/model` — picks and persists per role.

`smol` powers exploratory subagents (cheap & fast). `slow`/`plan` power architectural reasoning.

### 8. Verified behavior (test matrix)

Ran a series of `omp -p` (non-interactive) prompts on this machine after install. Results:

| Test                                                                  | Model                          | Result |
| --------------------------------------------------------------------- | ------------------------------ | :----: |
| `--no-tools "Reply with exactly one word: PONG"`                      | `ollama/qwen3-coder:30b`       |   ✅   |
| `"Read @.../embeddings/index.py and summarize in one sentence"`       | `ollama/qwen3-coder:30b`       |   ✅   |
| `--no-tools` arithmetic reasoning                                     | `ollama/qwen3-coder:30b`       |   ✅   |
| Tool-use required (model must invoke `bash`/`ls` to answer)           | `ollama/qwen3-coder:30b`       |   ❌ hallucinated a fake monorepo listing |
| Tool-use required                                                     | `ollama/qwen3-coder-next:latest` (79.7B) | ❌ timed out — model too large to be interactive |
| Tool-use required, `--no-extensions`                                  | `ollama/qwen3-coder:30b`       | ❌ still timed out at 180s |
| `--no-tools "Reply with exactly one word: PONG"`                      | `ollama/llama3.1:latest`       | ❌ hallucinated a tool call to a non-existent `irc.list` tool |

#### Conclusions

1. **`omp` itself works.** Install, Ollama provider, model discovery, file ingestion (`@path`), text-only inference, and CLI plumbing all behave correctly.
2. **Local models ≤ 30B are unreliable for agentic tool use in omp.** They either hallucinate tool calls (`llama3.1`, `qwen3-coder:30b` inventing `ls` output) or stall trying to drive omp's tool schema. omp is designed for Claude/GPT-4-class agentic behavior; small local models can't keep up within a reasonable budget.
3. **`@path` injection is the right pattern for local models.** When you pre-stuff context yourself, the model just needs to *read and reason*, which it does well.
4. **MCP-server load storm at every cold start.** omp inherits the global Claude Code MCP config. On this machine that means 11 servers (Atlassian, GitHub, Sentry, Linear, Glean, Figma, Buildkite, Klaviyo, etc.) all OAuth-fail with HTTP 401 every launch, and `npx mcp-remote ...` fails ENOENT. Logs are noisy in `~/.omp/logs/`. Pass `--no-extensions` to skip discovery, or prune the MCP config.
5. **Ollama memory runaway when stacking timeouts.** During this round of testing the `qwen3-coder-next:latest` (79.7B, ~54 GB VRAM) timed out and was killed by `omp`'s wrapper, but Ollama did **not** release the model — the process stayed pinned at ~50–57 GB resident. Stacking more `omp -p` invocations made it worse. **Mitigation:** if you're running non-interactive tests, kill the Ollama model child process between rounds (`pkill -f "Ollama.app.*Resources"` or `kill <PID>` from `ps aux | grep Ollama`). For interactive use, the TUI keeps a single model warm across turns and avoids this.

#### Failure mode analysis: model-normal vs. setup-specific

| Failure | Normal for these models? | Specific to our setup? |
| --- | --- | --- |
| `llama3.1` hallucinating tool calls (the fake `irc.list`) | **Yes** — `llama3.1` is weak at function-calling. Berkeley Function-Calling Leaderboard puts ≤8B Llama variants below 65% on tool accuracy. Any agent harness will hit this. | No |
| `qwen3-coder:30b` hallucinating `ls` output in omp | **Partly normal** at 30B. Berkeley's leaderboard puts mid-tier 30B coders around 70–80% on function-calls. **But** this same model + same Ollama backend ran the tool call correctly in opencode (real `ls` output, see `../opencode-first__ai/`). Same model, different harness, different result. | **Yes (the MCP storm).** omp loaded ~11 broken MCP servers (HTTP 401 / ENOENT) into the tool list every launch; the polluted schema almost certainly degraded tool selection. |
| 180s+ timeouts on tool-using turns | **Largely normal** — 30B Q4_K_M on M2 Max decodes ~5–15 tok/s. A tool-using turn easily emits 200–800 output tokens × ~3 turns of internal reasoning + tool args + post-tool synthesis. 180s is genuinely tight. | Partly — the timeout I picked was too short. 300–600s is realistic for local 30B agents. |
| `qwen3-coder-next` (79.7B) timing out | Expected — it barely fits in 64 GB unified memory and is too slow for interactive turns. Not a bug, a sizing mismatch. | Yes (we tried it anyway) |
| Ollama pinning 50–57 GB after client kill | **Known Ollama behavior** with very-long-context models (`qwen3-coder-next` allocates a 262K-token KV cache). Documented across the Ollama issue tracker. | Partly — fixable with `OLLAMA_KEEP_ALIVE=0` or `OLLAMA_KEEP_ALIVE=30s` to force eviction. |

**Roughly half the failures are inherent model limits at this size class; the other half are config issues we can fix** (MCP cleanup + `OLLAMA_KEEP_ALIVE` + longer client timeouts).

#### Re-verification (2026-05-04, after Ollama restart with cleared memory)

Smaller, faster retest after the runaway-kill:

```
$ omp -p --no-session --no-tools --no-extensions --model ollama/mistral:latest "What is 2+2? Reply with just the number."
4
```

Confirms omp's basic Q&A path is healthy on the smallest viable Ollama model. Same prompt under opencode's `plan` agent went off-prompt (documented in `../opencode-first__ai/README.md`); under omp with `--no-tools --no-extensions` it's clean. omp's plain-Q&A path is robust as long as you bypass the MCP storm and don't ask local models to drive tools.

For local-first-with-cloud-fallback, hybrid Ollama + Anthropic:

```bash
# ~/.zshrc
export ANTHROPIC_API_KEY=sk-ant-...
export PI_DEFAULT_MODEL=anthropic/claude-opus-4-7    # agentic tool use
export PI_SMOL_MODEL=ollama/llama3.1:latest          # cheap exploration subagents
export PI_PLAN_MODEL=anthropic/claude-opus-4-7       # architectural reasoning
```

For pure-local (no cloud), accept the trade-off:

```bash
export PI_DEFAULT_MODEL=ollama/qwen3-coder:30b
export PI_SMOL_MODEL=ollama/llama3.1:latest
# Always pass --no-tools for Q&A; reserve tool-using sessions for cloud models.
```

Suggested launcher alias to skip the MCP storm and the slow extension discovery:

```bash
alias omp='omp --no-extensions'
```

### 9. Optional Python tool

If you want the IPython kernel tool (lets the agent execute Python with file/search helpers):
```bash
omp setup python
```

---

## Why bother (vs. aider already in `ollama-pi-coding-agent-first__ai/`)

| Capability                       | aider | omp |
| -------------------------------- | :---: | :-: |
| Local Ollama models              |  ✅   | ✅  |
| Cloud providers (Anthropic etc.) |  ✅   | ✅  |
| TUI with sessions / branching    |  ❌   | ✅  |
| LSP integration (diagnostics, rename, refs) | ❌   | ✅  |
| MCP server support               |  ❌   | ✅  |
| Custom TS slash commands         |  ❌   | ✅  |
| Subagent / parallel task system  |  ❌   | ✅  |
| AI commit generation             |  ✅ (limited) | ✅  |
| Time-traveling streamed rules (TTSR) | ❌   | ✅  |

Trade-off: heavier to install (needs Bun) and more moving parts than aider, but feature parity with Claude Code / Cursor for local-first workflows.

---

## How this slots in with the rest of the monorepo

- **GitNexus MCP** — already wired. `omp` discovers MCP servers, so once installed it can call `gitnexus.impact`, `gitnexus.query`, etc. for structural queries.
- **Embedding index** in `../ollama-pi-coding-agent-first__ai/embeddings/` — currently a CLI (`search.py`). To expose it to `omp` natively, wrap it as a custom slash command at `~/.omp/agent/commands/embed-search/index.ts` that shells out to `python3 .../search.py --json` and returns the snippets. Out of scope for this folder; documented as a follow-up.

---

## Files in this folder
- `README.md` — this guide
- `setup.sh` — one-shot installer (Bun + omp + first-run config)
- `env.sample` — env vars for Ollama + optional cloud providers

---

## Open follow-ups
1. Decide which terminal we're standardizing on (iTerm2 is already installed and works out of the box — easiest).
2. Wrap the existing `embeddings/search.py` as an `omp` custom slash command so retrieval is one keystroke inside the TUI.
3. Decide a default project context file (`.omp/AGENTS.md` or similar) for the monorepo root so `omp` picks up house rules automatically.
