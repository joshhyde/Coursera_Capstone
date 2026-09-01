#!/usr/bin/env bash
# Diagnose dashboard issues on Mac mini.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${PORT:-8787}"

red() { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
bold() { printf '\033[1m%s\033[0m\n' "$*"; }

bold "Gridiron Edge doctor"
echo "Project: $ROOT"
echo ""

bold "1. Python / venv"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  green "OK  $("$ROOT/.venv/bin/python" --version)"
else
  red "MISSING  .venv — run ./scripts/setup-mac-mini.sh"
fi

bold "2. .env"
if [[ -f .env ]]; then
  green "OK  .env exists"
  grep -E '^HOST=|^PORT=|^ODDSPAPI_API_KEY=' .env | sed 's/ODDSPAPI_API_KEY=.*/ODDSPAPI_API_KEY=***redacted***/'
else
  red "MISSING  .env"
fi

bold "3. launchd service"
if launchctl print "gui/$(id -u)/com.gridiron-edge.serve" &>/dev/null; then
  green "OK  com.gridiron-edge.serve is loaded"
  launchctl print "gui/$(id -u)/com.gridiron-edge.serve" 2>/dev/null | grep -E 'state =|pid =|last exit' || true
else
  red "NOT LOADED  run: ./scripts/setup-mac-mini.sh"
fi

bold "4. Port $PORT"
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN &>/dev/null; then
  green "OK  something is listening on port $PORT"
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
else
  red "NOT LISTENING  dashboard is not running on port $PORT"
fi

bold "5. HTTP check"
if curl -sf -o /dev/null -m 3 "http://127.0.0.1:$PORT/"; then
  green "OK  http://127.0.0.1:$PORT/ responds"
else
  red "FAIL  http://127.0.0.1:$PORT/ not reachable"
fi

bold "6. Recent errors (last 20 lines)"
if [[ -f /tmp/gridiron-edge-serve.err ]]; then
  tail -20 /tmp/gridiron-edge-serve.err
else
  echo "(no error log yet)"
fi

echo ""
bold "Quick fixes"
echo "  Restart dashboard:  launchctl kickstart -k gui/\$(id -u)/com.gridiron-edge.serve"
echo "  Run manually:       cd $ROOT && ./scripts/run-serve.sh"
echo "  Reinstall services: ODDSPAPI_API_KEY=your-key ./scripts/setup-mac-mini.sh"
