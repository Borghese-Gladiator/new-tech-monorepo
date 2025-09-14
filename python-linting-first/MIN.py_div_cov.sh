#!/usr/bin/env bash
set -euo pipefail
MAIN_BRANCH="${MAIN_BRANCH:-origin/main}"
FAIL_UNDER="${FAIL_UNDER:-80}"       # overall diff coverage floor
CRITICAL_GLOBS="${CRITICAL_GLOBS:-app/auth/**,app/payments/**}" # 100% on these

# Run tests with coverage XML
pytest --maxfail=1 -q --cov=. --cov-report=xml --cov-report=term-missing

# Ensure we can compare to the base branch
git rev-parse --verify "$MAIN_BRANCH" >/dev/null 2>&1 || git fetch origin main:refs/remotes/origin/main || true

echo "→ Enforcing diff coverage ≥ ${FAIL_UNDER}%"
diff-cover coverage.xml --compare-branch="$MAIN_BRANCH" --fail-under="$FAIL_UNDER"

IFS=',' read -ra GLOBS <<< "$CRITICAL_GLOBS"
for g in "${GLOBS[@]}"; do
  if git diff --cached --name-only -- "$g" | grep -q .; then
    echo "→ Enforcing 100% diff coverage on critical path: $g"
    diff-cover coverage.xml --compare-branch="$MAIN_BRANCH" --include "$g" --fail-under=100
  fi
done
echo "✓ Diff coverage OK"
