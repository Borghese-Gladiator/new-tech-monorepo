#!/usr/bin/env bash
# Verification matrix for opencode + local Ollama on this machine.
# Mirrors the tests in oh-my-pi-first__ai/ so the two agents are comparable.
#
# Each test runs `opencode run` non-interactively against a model, with a
# timeout, and dumps the result into verification.log.
#
# Usage: bash run-tests.sh
set -uo pipefail

LOG="$(dirname "$0")/verification.log"
MODEL="ollama/qwen3-coder:30b"
TIMEOUT=180

: > "$LOG"

run_test_simple() {
  local label="$1"; shift
  local extra_flag="$1"; shift
  local prompt="$1"; shift
  {
    echo "================================================================="
    echo "TEST: $label"
    echo "MODEL: $MODEL  EXTRA: $extra_flag  TIMEOUT: ${TIMEOUT}s"
    echo "PROMPT: $prompt"
    echo "----- output -----"
  } | tee -a "$LOG"
  local start end rc
  start=$(date +%s)
  if [ -n "$extra_flag" ]; then
    # shellcheck disable=SC2086
    timeout "$TIMEOUT" opencode run -m "$MODEL" $extra_flag "$prompt" 2>&1 | tee -a "$LOG"
    rc=${PIPESTATUS[0]}
  else
    timeout "$TIMEOUT" opencode run -m "$MODEL" "$prompt" 2>&1 | tee -a "$LOG"
    rc=${PIPESTATUS[0]}
  fi
  end=$(date +%s)
  {
    echo "----- /output (exit=$rc, $((end - start))s) -----"
    echo ""
  } | tee -a "$LOG"
}

cd "$(dirname "$0")"

# 1. Plain Q&A — no tool use, no file context. Tests basic provider wiring.
run_test_simple "1. Plain Q&A (PONG)" "--agent plan" \
  "Reply with exactly one word: PONG"

# 2. File ingestion + summarize — uses opencode's -f to attach a file.
INDEX_PY="../ollama-pi-coding-agent-first__ai/embeddings/index.py"
if [ -f "$INDEX_PY" ]; then
  run_test_simple "2. File ingest + summarize" "--agent plan -f $INDEX_PY" \
    "Summarize in ONE sentence what this script does."
else
  echo "SKIP test 2: $INDEX_PY not found" | tee -a "$LOG"
fi

# 3. Reasoning — pure logic, no tools, no files.
run_test_simple "3. Arithmetic reasoning" "--agent plan" \
  "I have 3 apples and 2 oranges. I eat 1 apple. How many pieces of fruit do I have left? Reply with one number, nothing else."

# 4. Tool-use required — model must call bash/list to answer truthfully.
run_test_simple "4. Tool use (list directory)" "" \
  "Use a tool to list the actual files in $(pwd). Reply with only the filenames as a bulleted list. Do not invent files."

echo "Done. Full log: $LOG"
