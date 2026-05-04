#!/usr/bin/env bash
# One-shot setup for Ollama + Pi on macOS.
# Run: bash setup.sh
set -euo pipefail

MODEL="${MODEL:-mistral}"  # override: MODEL=codellama bash setup.sh

echo "==> Installing Ollama (if missing)"
if ! command -v ollama >/dev/null 2>&1; then
  brew install ollama
else
  echo "ollama already installed: $(ollama --version || true)"
fi

echo "==> Starting Ollama in the background (if not already running)"
if ! pgrep -x ollama >/dev/null 2>&1; then
  nohup ollama serve >/tmp/ollama.log 2>&1 &
  sleep 2
fi

echo "==> Pulling model: $MODEL"
ollama pull "$MODEL"

echo "==> Installing Pi agent"
if ! command -v pi >/dev/null 2>&1; then
  pip install pi-agent || {
    echo "pip install failed — install Pi manually from source:"
    echo "  git clone https://github.com/<pi-repo>.git && cd pi && pip install -e ."
    exit 1
  }
fi

echo "==> Exporting env vars (this shell only)"
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export PI_MODEL="$MODEL"

echo
echo "Done. Next steps:"
echo "  1. cd into your project"
echo "  2. Run: pi   (or: pi chat)"
echo "  3. To make env vars permanent, append env.sample contents to ~/.zshrc"
