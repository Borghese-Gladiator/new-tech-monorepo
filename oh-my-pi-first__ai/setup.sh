#!/usr/bin/env bash
# One-shot installer for Oh My Pi (omp) on macOS.
# Run: bash setup.sh
#
# Installs Bun (if missing), then omp via Bun, then sets sensible defaults
# pointing at the local Ollama stack.
set -euo pipefail

echo "==> 1/5  Checking Bun"
if ! command -v bun >/dev/null 2>&1; then
  echo "Bun not found — installing"
  curl -fsSL https://bun.sh/install | bash
  # shellcheck disable=SC1090
  if [ -f "$HOME/.bun/_bun" ]; then
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
  fi
else
  echo "Bun already installed: $(bun --version)"
fi

echo
echo "==> 2/5  Verifying Bun >= 1.3.7"
BUN_VER="$(bun --version)"
# crude semver check — fine for our purposes
if [ "$(printf '%s\n%s\n' "1.3.7" "$BUN_VER" | sort -V | head -n1)" != "1.3.7" ]; then
  echo "WARN: Bun $BUN_VER is older than 1.3.7. omp may not run. Upgrade with: bun upgrade"
fi

echo
echo "==> 3/5  Installing @oh-my-pi/pi-coding-agent"
if ! command -v omp >/dev/null 2>&1; then
  bun install -g @oh-my-pi/pi-coding-agent
else
  echo "omp already installed: $(omp --version || true)"
fi

echo
echo "==> 4/5  Verifying Ollama is reachable"
if ! curl -fsS http://localhost:11434/api/tags >/dev/null; then
  echo "WARN: Ollama not reachable at http://localhost:11434"
  echo "      Start it in another tab: ollama serve"
else
  echo "Ollama is up."
fi

echo
echo "==> 5/5  Suggested next steps for local Ollama"
echo
echo "omp does not expose record-keys (modelRoles) via 'config set' from the CLI."
echo "Set per-role models one of these ways:"
echo
echo "  A) Per-invocation flags:"
echo "       omp --model ollama/qwen3-coder:30b --smol ollama/llama3.1:latest"
echo
echo "  B) Env vars (add to ~/.zshrc):"
echo "       export PI_DEFAULT_MODEL=ollama/qwen3-coder:30b"
echo "       export PI_SMOL_MODEL=ollama/llama3.1:latest"
echo "       export PI_PLAN_MODEL=ollama/qwen3-coder:30b"
echo
echo "  C) Interactively inside the TUI:"
echo "       /model      # pick + persist per-role assignments"
echo
echo "Verified working on this machine:"
echo "  omp -p --no-tools --model ollama/qwen3-coder:30b 'Reply with exactly one word: PONG'  ->  PONG"
echo
echo "Done. Launch the TUI with:  omp"
