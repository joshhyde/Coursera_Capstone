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

if grep -qE '^HOST=(127\.0\.0\.1|localhost)' .env 2>/dev/null; then
  red "HOST is loopback — phones and iPads cannot connect. Set HOST=0.0.0.0"
fi

bold "4. Port $PORT"
LISTEN_ADDR=""
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN &>/dev/null; then
  green "OK  something is listening on port $PORT"
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
  LISTEN_ADDR="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN | awk 'NR>1 {print $9}')"
  if echo "$LISTEN_ADDR" | grep -q '127.0.0.1'; then
    red "BOUND TO LOCALHOST ONLY — phones cannot connect. HOST must be 0.0.0.0"
  fi
else
  red "NOT LISTENING  dashboard is not running on port $PORT"
fi

bold "5. HTTP check"
if curl -sf -o /dev/null -m 3 "http://127.0.0.1:$PORT/"; then
  green "OK  http://127.0.0.1:$PORT/ responds"
else
  red "FAIL  http://127.0.0.1:$PORT/ not reachable"
fi

bold "6. Phone / iPad URLs (same Wi-Fi, type http:// not https://)"
echo "Do not open http://0.0.0.0:$PORT or http://localhost:$PORT on the phone."
echo "Those only work on this Mac. Guest Wi-Fi, VPN, and cellular will also fail."
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  "$ROOT/.venv/bin/python" - <<PY || true
from gridiron_edge.lan import phone_urls
from gridiron_edge.config import get_settings
s = get_settings()
print(f"This Mac:  http://127.0.0.1:{s.port}")
urls = phone_urls(s.port)
if urls:
    print("Phone / iPad:")
    for u in urls:
        print(f"  {u}")
else:
    print("Could not detect a LAN IP. System Settings → Network, or: ipconfig getifaddr en0")
PY
else
  echo "(venv missing — cannot print URLs from Python)"
fi
if command -v ipconfig &>/dev/null; then
  echo "Interface IPs:"
  for iface in en0 en1 en2 bridge0; do
    ip=$(ipconfig getifaddr "$iface" 2>/dev/null || true)
    if [[ -n "${ip:-}" ]]; then
      echo "  http://$ip:$PORT  ($iface)"
    fi
  done
fi
if [[ -x /usr/libexec/ApplicationFirewall/socketfilterfw ]]; then
  /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || true
  echo "If firewall is on: System Settings → Network → Firewall → Options → allow Python"
fi

bold "7. Recent errors (last 20 lines)"
if [[ -f /tmp/gridiron-edge-serve.err ]]; then
  tail -20 /tmp/gridiron-edge-serve.err
else
  echo "(no error log yet)"
fi

echo ""
bold "Quick fixes"
echo "  Restart dashboard:  launchctl kickstart -k gui/\$(id -u)/com.gridiron-edge.serve"
echo "  Print phone URLs:   cd $ROOT && .venv/bin/gridiron urls"
echo "  Run manually:       cd $ROOT && ./scripts/run-serve.sh"
echo "  Reinstall services: ODDSPAPI_API_KEY=your-key ./scripts/setup-mac-mini.sh"
