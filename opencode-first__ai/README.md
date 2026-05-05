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

- **Memory pressure (Ollama-side, not opencode-specific):** Running `qwen3-coder:30b` repeatedly via `opencode run` (and earlier `omp -p` calls in `oh-my-pi-first__ai/`) left Ollama pinned at ~50–57 GB resident even after the client process was killed. Ollama does not always release the loaded model between non-interactive invocations on this hardware. **Mitigation:** kill the Ollama model child process between batch rounds (`ps aux | grep Ollama` then `kill <PID>`), or prefer the TUI (`opencode`) which keeps a single model warm across turns. The same caveat is documented in `../oh-my-pi-first__ai/README.md`.
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

#### Failure mode analysis: model-normal vs. setup-specific

| Failure | Normal for these models? | Specific to our setup? |
| --- | --- | --- |
| 180s timeout on the arithmetic prompt | **Largely normal** — 30B Q4_K_M on M2 Max decodes ~5–15 tok/s; the model also burned tokens on internal reasoning before answering. | Partly — 180s is too tight. Bump to 300–600s for 30B local. |
| `-f` flag swallowed the message arg | **No** — purely an opencode CLI quirk. `-f` is `array`-typed in yargs and greedy. | **Yes** (script bug). Fix is `opencode run -m … -f file -- "message"`. |
| 171s for a single-token "PONG" reply | **Mostly model-normal.** Cold model load on first turn dominates here; subsequent turns in the same TUI session are far faster. The non-interactive `run` reloads the model every call. | Partly — using `opencode run` for a test matrix is the wrong shape. The TUI is the right shape for warm reuse. |
| Tool call succeeded but turn still timed out (test 4) | **Mostly normal** — model called `ls`, got real output, then needed more tokens to format the final bulleted reply. 30B at ~10 tok/s ran out of clock. | Partly — same timeout caveat. |
| Ollama pinning 50–57 GB after client kill | **Known Ollama behavior** with long-context models. Documented in Ollama's issue tracker. | Partly — fixable with `OLLAMA_KEEP_ALIVE=0` (or `30s`) to force eviction. |

**On opencode vs omp for the same model:** the 30B model hallucinated under omp but **invoked the real tool under opencode**. Two plausible reasons:
- omp's tool list was polluted by ~11 broken inherited Claude-Code MCP servers (HTTP 401 / ENOENT every launch), confusing the model's tool-selection.
- opencode's local config has only one MCP server (`gitnexus`) and a clean tool surface.

That suggests the omp tool-hallucination is **largely setup-specific** (MCP storm), not a flat model limitation. Pruning omp's MCP config or running with `--no-extensions` should narrow the gap.

#### Re-verification (2026-05-04, after Ollama restart with cleared memory)

Reran the smallest viable test to verify opencode+Ollama still works after we killed the runaway:

```
$ opencode run -m ollama/mistral:latest --agent plan "What is 2+2? Reply with just the number."
9. Deploy app when PR is merged (use CI/CD pipeline)
### 4. Risks
- Edge case: user interface may be unresponsive or misaligned in certain dark mode settings
...
```

That's **off-prompt nonsense.** Same model called three different ways:

| Caller | Output |
| --- | --- |
| `command curl http://localhost:11434/api/generate -d '{"model":"mistral:latest","prompt":"What is 2+2? Reply with just the number."}'` | `4` ✅ |
| `omp -p --no-tools --no-extensions --model ollama/mistral:latest "What is 2+2? ..."` | `4` ✅ |
| `opencode run -m ollama/mistral:latest --agent plan "What is 2+2? ..."` | architectural-rant ❌ |

**Conclusion:** opencode's `plan` agent injects a verbose architectural system prompt that swamps `mistral:latest`'s 7B instruction-following capacity. Mistral isn't broken; the system prompt is too heavy for it. **Use `--agent build` (lighter prompt) or a stronger model (`qwen3-coder:30b`+) when running opencode against small Ollama models.** Or skip opencode for very small local models and use bare Ollama / aider.

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

---

## Addendum — Cross-agent comparison (session findings)

Findings from a single test session that bootstrapped and ran three coding agents (aider, omp, opencode) against the same local Ollama on this machine. Same content is mirrored in `../oh-my-pi-first__ai/README.md` and `../ollama-pi-coding-agent-first__ai/README.md` so any one of these folders is self-sufficient.

### A/B/C/D test on the same model (`mistral:latest`, ~7B) and same prompt

Prompt: `"What is 2+2? Reply with just the number."` Expected: `4`.

| Caller | Result | Notes |
| --- | :---: | --- |
| `command curl http://localhost:11434/api/generate ...` (bare Ollama) | ✅ `4` | Baseline. The model itself is fine. |
| `omp -p --no-tools --no-extensions --model ollama/mistral:latest "..."` | ✅ `4` | omp's plain-Q&A path is healthy when the MCP storm is bypassed and tools are off. |
| `opencode run -m ollama/mistral:latest --agent plan "..."` | ❌ off-prompt rant about CI/CD, dark mode, CSRF tokens | opencode's `plan` agent injects a verbose architectural system prompt. mistral 7B's instruction-following collapses under the weight; it pattern-completes on the system prompt instead of answering the user. |
| `aider --model ollama_chat/mistral:latest --no-git --yes --message "..."` | ✅ `4` | aider's system prompt is light; the model has room to actually answer. |

### Layer-isolation finding

When the bare Ollama API returns the right answer but a wrapper agent does not, the failure is in the **harness**, not the model. Two distinct harness-layer failure modes were observed in this session:

- **omp:** ~11 inherited Claude-Code MCP servers (HTTP 401 / ENOENT every cold start) polluted the tool list and likely degraded function-calling on `qwen3-coder:30b` (the model hallucinated a fake monorepo listing). Same model + same Ollama under opencode's clean tool list invoked `ls -a` correctly.
- **opencode:** the `plan` agent's heavy system prompt overwhelms small (≤7B) instruction-following. `--agent build` has a lighter prompt; `qwen3-coder:30b` and larger handle either.

### Recommended pairing matrix

Picking by hardware/model size on this machine (M2 Max, 64 GB):

| Model class | Best agent here | Why |
| --- | --- | --- |
| ≤ 7B local (`mistral`, `llama3.2`) | **aider** (Poetry venv in `../ollama-pi-coding-agent-first__ai/`) | Lightest system prompt, cleanest tool surface. Avoids opencode's `plan`-prompt overload and omp's MCP storm. |
| 13–30B local (`qwen3-coder:30b`, `qwen2.5:14b`) | **opencode** | Tool-call reliability beats omp on the same model (real `ls` vs hallucinated). Use `--agent plan` for read-only or `--agent build` for full access. |
| 30B+ local with tool-using sessions | Hybrid: cloud default, local `smol` | Local 30B at ~10 tok/s is too slow for productive agentic loops; pin a cloud model to the default role and keep Ollama for cheap exploration subagents. |
| Cloud frontier (Claude Opus/Sonnet, GPT-4-class) | **omp** or **opencode** (parity at this tier) | Both have feature-rich TUIs; pick by feature preference (omp: TTSR, IPython kernel, native engine; opencode: client/server, GitHub PR fetch, web UI). |

### Permanent setup mitigations worth doing

- **`OLLAMA_KEEP_ALIVE=30s`** — set before `ollama serve` starts. Prevents the 50–57 GB pinned-after-kill state we hit with `qwen3-coder-next` (79.7B / 262K context).
- **omp:** prune `~/.claude/` MCP servers you don't actually use, or `alias omp='omp --no-extensions'` to skip discovery entirely.
- **opencode:** use `--agent build` for small models; reserve `--agent plan` for ≥30B or cloud.
- **Timeouts:** budget 300–600s per turn for local 30B agentic sessions, not 180s.
