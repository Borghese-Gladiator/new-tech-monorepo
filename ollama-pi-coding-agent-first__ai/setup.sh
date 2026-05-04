#!/usr/bin/env bash
# One-shot setup for Ollama + aider on macOS, Poetry-based.
# Run: bash setup.sh
set -euo pipefail

MODEL="${MODEL:-mistral}"  # override: MODEL=codellama bash setup.sh

# Resolve this script's directory so we always operate on the right project.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

echo "==> Verifying Ollama is reachable on http://localhost:11434"
if ! curl -sf http://localhost:11434/api/tags >/dev/null; then
  echo "ERROR: Ollama is not reachable on localhost:11434. Try 'ollama serve' in another tab."
  exit 1
fi

echo "==> Pulling model: $MODEL"
ollama pull "$MODEL"

echo "==> Verifying Poetry is installed"
if ! command -v poetry >/dev/null 2>&1; then
  echo "ERROR: Poetry is not installed."
  echo "Install per-user (no system pollution):"
  echo "  curl -sSL https://install.python-poetry.org | python3 -"
  echo "Then re-run: bash setup.sh"
  exit 1
fi
echo "poetry: $(poetry --version)"

echo "==> Installing project dependencies via Poetry (creates ./.venv/)"
poetry --directory="$SCRIPT_DIR" install

echo
echo "Done. Next steps:"
echo "  1. cd $SCRIPT_DIR"
echo "  2. Run aider against Ollama (no global install needed):"
echo "       poetry run aider --model ollama_chat/$MODEL"
echo "  3. To make env vars permanent, append env.sample contents to ~/.zshrc"
echo "  4. To use the embedding index:"
echo "       poetry run python embeddings/index.py --stats"
echo "       poetry run python embeddings/search.py --k 5 \"your query\""
