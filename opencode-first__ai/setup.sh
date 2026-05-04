#!/usr/bin/env bash
# Setup checker for opencode + local Ollama.
# Verifies install, checks Ollama, and ensures ~/.config/opencode/opencode.json
# has an "ollama" provider entry. Does NOT install opencode for you — install
# directions are in README.md.
set -euo pipefail

CONFIG="$HOME/.config/opencode/opencode.json"

echo "==> 1/4  Checking opencode"
if ! command -v opencode >/dev/null 2>&1; then
  echo "opencode is NOT installed. Install with one of:"
  echo "  brew install anomalyco/tap/opencode"
  echo "  brew install opencode"
  echo "  curl -fsSL https://opencode.ai/install | bash"
  echo "  npm i -g opencode-ai@latest"
  exit 1
fi
echo "opencode: $(opencode --version)"

echo
echo "==> 2/4  Checking Ollama"
if ! curl -fsS -m 2 http://localhost:11434/api/tags >/dev/null; then
  echo "WARN: Ollama not reachable at http://localhost:11434"
  echo "      Start it: ollama serve"
else
  echo "Ollama is up."
fi

echo
echo "==> 3/4  Checking opencode config has ollama provider"
if [ ! -f "$CONFIG" ]; then
  echo "Config not found at $CONFIG — opencode will create it on first run."
  echo "To wire Ollama, add the snippet from README.md to that file."
  exit 0
fi

if grep -q '"ollama"' "$CONFIG"; then
  echo "ollama provider already configured in $CONFIG"
else
  echo "ollama provider NOT found in $CONFIG"
  echo "Add this block under \"provider\":"
  cat <<'JSON'
  "ollama": {
    "npm": "@ai-sdk/openai-compatible",
    "name": "Local Ollama",
    "options": { "baseURL": "http://127.0.0.1:11434/v1" },
    "models": {
      "qwen3-coder:30b":   { "limit": { "context": 200000, "output": 8192 } },
      "llama3.1:latest":   { "limit": { "context": 128000, "output": 8192 } },
      "mistral:latest":    { "limit": { "context":  32000, "output": 8192 } }
    }
  }
JSON
fi

echo
echo "==> 4/4  Listing models opencode currently sees"
opencode models 2>&1 | head -20

echo
echo "Done. Run the verification matrix with:  bash run-tests.sh"
