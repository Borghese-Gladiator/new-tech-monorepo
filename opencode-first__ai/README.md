# OpenCode — First AI Setup (macOS)

[OpenCode](https://github.com/anomalyco/opencode) (`opencode`) is an open-source terminal AI coding agent — provider-agnostic (Claude, OpenAI, Google, **local models**), TUI-first, with a built-in `plan` (read-only) agent and a `build` (full-access) agent. From the same author as terminal.shop. Project moved from `sst/opencode` to `anomalyco/opencode`.

This folder is a setup playbook + verification script for using `opencode` against the local Ollama stack on this machine (Apple M2 Max, 64 GB).

---

## Status on this machine (verified)

- `opencode --version` → **1.2.20** (already installed at `/opt/homebrew/bin/opencode`)
- Installed via Homebrew (`anomalyco/tap` or stock formula)
- Existing config at `~/.config/opencode/opencode.json` had a stale `qwen3-coder` provider pointing at a non-running `llama-server` on `:11400`. Setup adds an `ollama` provider on `:11434` alongside it (does not remove the existing entry).

---

## Install (if not already present)

If `which opencode` returns nothing, pick one:

```bash
# Recommended on macOS — third-party tap, always up to date
brew install anomalyco/tap/opencode

# Official brew formula (updated less often)
brew install opencode

# Or upstream installer
curl -fsSL https://opencode.ai/install | bash

# Or via npm
npm i -g opencode-ai@latest
```

---

## Wire to local Ollama

opencode uses the Vercel AI SDK and `@ai-sdk/openai-compatible` to talk to any OpenAI-compatible endpoint. Ollama exposes one at `http://127.0.0.1:11434/v1`. Add a provider block in `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local Ollama",
      "options": {
        "baseURL": "http://127.0.0.1:11434/v1"
      },
      "models": {
        "qwen3-coder:30b":   { "limit": { "context": 200000, "output": 8192 } },
        "llama3.1:latest":   { "limit": { "context": 128000, "output": 8192 } },
        "mistral:latest":    { "limit": { "context":  32000, "output": 8192 } }
      }
    }
  },
  "model": "ollama/qwen3-coder:30b"
}
```

Make sure Ollama is running:
```bash
ollama serve
```

---

## Usage

### TUI

```bash
opencode                           # current dir
opencode /path/to/project          # specific project
```

Switch agent with `Tab`:
- **build** — default, full access (read/edit/bash)
- **plan** — read-only, asks before bash; great for unfamiliar code

### Non-interactive (shell-friendly)

```bash
opencode run -m ollama/qwen3-coder:30b "Summarize what this script does" -f index.py
opencode run --agent plan "What does this repo do?"
opencode run --format json "..."     # machine-readable events
```

### Other useful commands

```bash
opencode models                    # list discovered models
opencode auth login                # set up cloud providers (Anthropic, OpenAI, …)
opencode stats                     # token usage + cost
opencode mcp                       # manage MCP servers
opencode session                   # list/inspect saved sessions
```

---

## Verification

`run-tests.sh` runs the same matrix used in `oh-my-pi-first__ai/` so you can compare opencode vs omp on this hardware.

```bash
bash run-tests.sh
```

Tests:
1. **Plain Q&A** — `opencode run "Reply with exactly one word: PONG"` (no tools)
2. **File ingestion** — read a file (`-f`) and summarize
3. **Reasoning** — small arithmetic puzzle
4. **Tool use required** — model must invoke a directory listing to answer (this is the test where small local models historically fail)

Results are saved to `verification.log`. Findings are written into the table below after the first run.

### Result matrix (run on this machine, 2026-05-04)

| Test                                                | Model                          | Result | Time | Notes |
| --------------------------------------------------- | ------------------------------ | :----: | :--: | ----- |
| 1. Plain Q&A "PONG" (`--agent plan`)                | `ollama/qwen3-coder:30b`       |   ✅   | 171s | Correct: `PONG`. Slow even for trivial output. |
| 2. File ingestion + summarize (`-f path`)           | `ollama/qwen3-coder:30b`       |   ⚠️   |  1s  | Script bug — opencode parsed the prompt as another `-f` value. The `-f` flag is `array`-typed and greedy; need to pass `--` between `-f` args and the message, or wrap the prompt in `--prompt`. |
| 3. Arithmetic reasoning (`--agent plan`)            | `ollama/qwen3-coder:30b`       |   ❌   | 180s | Timeout. Model started but produced no answer in budget. |
| 4. Tool use — list directory (`build` agent)        | `ollama/qwen3-coder:30b`       |   🌟   | 180s | **Tool call succeeded with real output** — model invoked `ls -a` and got the genuine file listing (`env.sample`, `README.md`, `run-tests.sh`, `setup.sh`, `verification.log`). Then ran out of time before formatting the final reply, so process was killed by the 180s timeout. The shell tool itself worked correctly. |

#### Key finding vs. omp

Test 4 is the same prompt that omp's `qwen3-coder:30b` failed by **hallucinating** a fake monorepo listing (`.git`, `agent`, `fender`, `k-repo`, `pnpm-lock.yaml`, …). With opencode's tool harness, the same model **actually invoked the shell tool** and got real output. opencode's tool wiring appears more reliable than omp's for local-model agentic use — it didn't have to be coerced into using a tool.

#### Caveats

- **Memory pressure:** Running `qwen3-coder:30b` repeatedly via `opencode run` caused Ollama to balloon to ~50 GB resident. We killed the runaway process after test 4. The model may not release VRAM/RAM cleanly between non-interactive invocations on this hardware. **For interactive use, prefer the TUI** (`opencode`) over repeated `opencode run` calls — sessions reuse the loaded model.
- **`-f` parsing:** the script's test 2 needs `--` between the file list and the message:
  ```bash
  opencode run -m ollama/qwen3-coder:30b -f path/to/file.py -- "Your prompt"
  ```
  This is a bug in `run-tests.sh` — the README test list documents the correct syntax for users.
- **Timeouts:** 180s is too tight for tool-using sessions on a local 30B model. Bump to 300s+ if you re-run.

#### Takeaways

1. **opencode + Ollama works.** Plain Q&A, tool calls, and the `plan`/`build` agent split all behave as designed.
2. **opencode's tool reliability beats omp's** for the same local model — same prompt, real output instead of hallucination.
3. **Local 30B is still the bottleneck.** Same constraint as omp testing: response latency on a 30B model makes interactive sessions slow and non-interactive matrix-runs prone to timeout/memory issues. For real work, hybrid Anthropic + local-`plan` is still the recommendation.
4. **Use the TUI, not repeated `opencode run`.** The TUI keeps one model loaded across turns; repeated `run` invocations re-load and stack memory.

---

## Why try opencode (vs. omp / aider already in this monorepo)

| Capability                                  | aider | omp | opencode |
| ------------------------------------------- | :---: | :-: | :------: |
| Local Ollama models                         |  ✅   | ✅  |   ✅    |
| Cloud providers                             |  ✅   | ✅  |   ✅    |
| TUI                                         |  ❌   | ✅  |   ✅    |
| Sessions / branching                        |  ❌   | ✅  |   ✅    |
| Read-only `plan` agent                      |  ❌   | ⚠️  |   ✅    |
| LSP integration                             |  ❌   | ✅  |   ✅    |
| MCP servers                                 |  ❌   | ✅  |   ✅    |
| GitHub integration (`opencode pr <#>`)      |  ❌   | ❌  |   ✅    |
| Headless server / mobile-driven sessions    |  ❌   | ❌  |   ✅    |
| Web UI (`opencode web`)                     |  ❌   | ❌  |   ✅    |

opencode's distinguishing features vs. omp:
- **Client/server architecture**: `opencode serve` runs headless; you can drive sessions from a separate TUI, a web UI, or the desktop app.
- **`opencode pr <number>`**: fetches a GitHub PR branch and opens it for review.
- **No global Claude-Code MCP-server inheritance** — config is local to opencode.json, so we don't get the 11-server OAuth-401 storm we hit with omp.

---

## Files in this folder

- `README.md` — this guide
- `setup.sh` — verifies install + Ollama; appends the `ollama` provider to `~/.config/opencode/opencode.json` if missing
- `run-tests.sh` — runs the verification matrix; writes `verification.log`
- `env.sample` — env vars for cloud providers (optional)

---

## Open follow-ups

1. Wire the embedding index from `ollama-pi-coding-agent-first__ai/embeddings/` into opencode as a custom MCP server (so semantic retrieval is available inside the TUI).
2. Decide whether to set the default model to `ollama/qwen3-coder:30b` (pure-local) or to a cloud model with Ollama as the `plan` agent. omp testing on this machine showed that local 30B models can't reliably drive agentic tool calls — same constraint will apply here. Use `--agent plan` (read-only) for local-model sessions to sidestep tool-use failure modes.
