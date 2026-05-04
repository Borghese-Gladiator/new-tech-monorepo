# Swapping Models (qwen-coder & friends)

Pi (and any OpenAI-compatible client) is model-agnostic. If Ollama can run it, you can use it.

## Recommendation for this machine

**Mac: M1, 64GB RAM**

- **Primary:** `qwen2.5-coder:32b` — best open coding model that fits comfortably. ~20GB RAM in use, ~15–25 tok/s on M1, plenty of headroom for IDE / Docker / browser.
- **Fallback:** `qwen2.5-coder:14b` — when you want snappier iteration or are running other heavy apps. ~9GB RAM, noticeably faster, still excellent quality.
- **Skip:** `:7b` (no reason with 64GB), 70B+ (will swap and crawl on M1).

## Use qwen-coder

Pull:
```bash
ollama pull qwen2.5-coder:32b      # primary
ollama pull qwen2.5-coder:14b      # fallback
```

Verify:
```bash
ollama run qwen2.5-coder:32b
```

Point Pi at it (same env vars as Ollama setup, just change the model):
```bash
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export PI_MODEL=qwen2.5-coder:32b
```

Or inside Pi:
```
/model qwen2.5-coder:32b
```

That's it. The OpenAI-compatible endpoint Ollama exposes (`localhost:11434/v1`) accepts any tag from `ollama list`.

## Other coding models worth trying

| Model | Pull tag | Notes |
|---|---|---|
| Qwen 2.5 Coder | `qwen2.5-coder` | Currently top open coding model |
| DeepSeek Coder V2 | `deepseek-coder-v2` | Strong, MoE, fast |
| Code Llama | `codellama` | Older but stable |
| Codestral | `codestral` | Mistral's coding model |
| Llama 3.1 | `llama3.1` | General, decent at code |

Sizes available for most: `:1.5b`, `:3b`, `:7b`, `:14b`, `:32b` (and sometimes `:70b`).

## RAM sizing rule of thumb (Apple Silicon)

| RAM | Sweet spot |
|---|---|
| 8GB | `:1.5b` or `:3b` |
| 16GB | `:7b` |
| 32GB | `:14b` |
| 64GB | **`:32b`** ← you are here |
| 128GB+ | `:70b` |

## Works with more than Pi

Anything that speaks OpenAI's API can point at `localhost:11434/v1`:

- **Aider** — `aider --model ollama/qwen2.5-coder:32b`
- **Continue.dev** — VS Code extension; set provider to Ollama
- **Cursor** — custom OpenAI base URL in settings
- **OpenCode**, **Cline**, **Roo Code**, etc.

## Quick switch script

To switch model for a shell session:
```bash
export PI_MODEL=qwen2.5-coder:14b   # or :32b
```

To make permanent, append to `~/.zshrc`.

## Tip: keep both pulled

Disk is cheaper than re-downloading. Pull `:14b` and `:32b` both — switch via `PI_MODEL` based on whether you want speed or quality that day.
