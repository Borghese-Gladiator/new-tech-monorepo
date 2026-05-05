#!/usr/bin/env bash
# Launch a dedicated Chrome instance with remote debugging enabled.
# Used by the chrome-devtools-mcp server (default port 9222).

set -euo pipefail

PORT="${PORT:-9222}"
PROFILE_DIR="${PROFILE_DIR:-/tmp/chrome-devtools}"
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome not found at: $CHROME_BIN" >&2
  echo "Edit CHROME_BIN in this script if Chrome is installed elsewhere." >&2
  exit 1
fi

echo "Launching Chrome with remote debugging on port $PORT"
echo "Profile dir: $PROFILE_DIR"
echo "Verify with: open http://localhost:$PORT/json"

exec "$CHROME_BIN" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR"
