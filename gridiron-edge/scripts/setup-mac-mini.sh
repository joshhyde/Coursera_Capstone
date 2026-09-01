#!/usr/bin/env bash
# One-shot Mac mini installer: deps, .env, launchd (dashboard + scheduled sync), LAN access.
#
# Usage:
#   ./scripts/setup-mac-mini.sh
#   ODDSPAPI_API_KEY=your-key ./scripts/setup-mac-mini.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PORT="${PORT:-8787}"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11

red() { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
bold() { printf '\033[1m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }

python_version_ok() {
  local py="$1"
  "$py" -c "import sys; raise SystemExit(0 if sys.version_info >= ($MIN_PYTHON_MAJOR, $MIN_PYTHON_MINOR) else 1)" 2>/dev/null
}

find_python() {
  local candidates=(
    python3.12 python3.11
    /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11
    /usr/local/bin/python3.12 /usr/local/bin/python3.11
    python3
  )
  local py
  for py in "${candidates[@]}"; do
    if command -v "$py" &>/dev/null && python_version_ok "$py"; then
      echo "$py"
      return 0
    fi
  done
  return 1
}

install_python_via_brew() {
  if ! command -v brew &>/dev/null; then
    red "Homebrew not found."
    echo "Install Homebrew first: https://brew.sh"
    echo "Then run: brew install python@3.12"
    exit 1
  fi
  yellow "Python 3.11+ not found. Installing python@3.12 via Homebrew..."
  brew install python@3.12
}

if [[ "$(uname)" != "Darwin" ]]; then
  red "This script is for macOS (Mac mini). Run install-mac.sh on other platforms."
  exit 1
fi

bold "==> Gridiron Edge Mac mini setup"
echo "Project: $PROJECT_DIR"

PYTHON=""
if ! PYTHON="$(find_python)"; then
  install_python_via_brew
  PYTHON="$(find_python)" || {
    red "Still no Python 3.11+. Run: brew install python@3.12"
    exit 1
  }
fi

PY_VERSION="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
green "Using Python $PY_VERSION ($PYTHON)"

cd "$PROJECT_DIR"

# Remove broken venv from a prior failed install (e.g. system Python 3.9)
if [[ -d "$VENV_DIR" ]]; then
  if ! "$VENV_DIR/bin/python" -c "import sys; raise SystemExit(0 if sys.version_info >= ($MIN_PYTHON_MAJOR, $MIN_PYTHON_MINOR) else 1)" 2>/dev/null; then
    yellow "Removing old .venv (wrong Python version)..."
    rm -rf "$VENV_DIR"
  fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtualenv..."
  "$PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -e ".[dev]"

mkdir -p "$HOME/.gridiron-edge"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

API_KEY="${ODDSPAPI_API_KEY:-${1:-}}"
if [[ -n "$API_KEY" ]]; then
  if grep -q '^ODDSPAPI_API_KEY=' .env; then
    sed -i '' "s|^ODDSPAPI_API_KEY=.*|ODDSPAPI_API_KEY=$API_KEY|" .env
  else
    echo "ODDSPAPI_API_KEY=$API_KEY" >> .env
  fi
  green "API key saved to .env"
elif grep -q 'your-key-here' .env 2>/dev/null; then
  red "No API key found. Re-run with:"
  echo "  ODDSPAPI_API_KEY=your-key ./scripts/setup-mac-mini.sh"
  exit 1
fi

if grep -q '^HOST=' .env; then
  sed -i '' 's|^HOST=.*|HOST=0.0.0.0|' .env
else
  echo "HOST=0.0.0.0" >> .env
fi

if grep -q '^PORT=' .env; then
  sed -i '' "s|^PORT=.*|PORT=$PORT|" .env
else
  echo "PORT=$PORT" >> .env
fi

bold "==> Installing launchd services (dashboard always on + sync 8am/4pm)"

install_plist() {
  local src="$1"
  local label="$2"
  local dest="$LAUNCH_AGENTS/$label.plist"
  sed \
    -e "s|__GRIDIRON_ROOT__|$PROJECT_DIR|g" \
    -e "s|__GRIDIRON_VENV__|$VENV_DIR|g" \
    "$src" > "$dest"
  plutil -lint "$dest" >/dev/null
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  sleep 1
  if ! launchctl bootstrap "gui/$(id -u)" "$dest" 2>/dev/null; then
    yellow "launchctl bootstrap failed for $label — trying load..."
    launchctl unload "$dest" 2>/dev/null || true
    launchctl load "$dest" 2>/dev/null || yellow "Could not auto-start $label (run ./scripts/run-serve.sh manually)"
  fi
  launchctl enable "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl kickstart -k "gui/$(id -u)/$label" 2>/dev/null || true
}

mkdir -p "$LAUNCH_AGENTS"
chmod +x "$SCRIPT_DIR/run-serve.sh" "$SCRIPT_DIR/run-sync.sh" "$SCRIPT_DIR/doctor.sh"
install_plist "$SCRIPT_DIR/com.gridiron-edge.serve.plist" "com.gridiron-edge.serve"
install_plist "$SCRIPT_DIR/com.gridiron-edge.sync.plist" "com.gridiron-edge.sync"

sleep 2
bold "==> Health check"
if curl -sf -o /dev/null -m 5 "http://127.0.0.1:$PORT/"; then
  green "Dashboard is responding on port $PORT"
else
  yellow "Dashboard not responding yet — check logs:"
  echo "  tail -30 /tmp/gridiron-edge-serve.err"
  echo "  ./scripts/doctor.sh"
  echo ""
  yellow "Trying manual start..."
  "$SCRIPT_DIR/run-serve.sh" &
  SERVE_PID=$!
  sleep 3
  if curl -sf -o /dev/null -m 5 "http://127.0.0.1:$PORT/"; then
    green "Manual start works — restarting launchd service..."
    kill "$SERVE_PID" 2>/dev/null || true
    launchctl kickstart -k "gui/$(id -u)/com.gridiron-edge.serve" 2>/dev/null || true
  else
    kill "$SERVE_PID" 2>/dev/null || true
    red "Dashboard still not responding. Run ./scripts/doctor.sh and share the output."
  fi
fi

bold "==> Initial odds sync"
"$VENV_DIR/bin/gridiron" sync || echo "(sync skipped — will retry on schedule)"

LAN_IP=""
for iface in en0 en1; do
  ip=$(ipconfig getifaddr "$iface" 2>/dev/null || true)
  if [[ -n "$ip" ]]; then
    LAN_IP="$ip"
    break
  fi
done

echo ""
green "Setup complete!"
echo ""
bold "Open the dashboard:"
echo "  On this Mac:     http://127.0.0.1:$PORT"
if [[ -n "$LAN_IP" ]]; then
  echo "  Other devices:   http://$LAN_IP:$PORT"
  echo "                   (same Wi‑Fi network required)"
else
  echo "  Other devices:   http://<mac-mini-ip>:$PORT"
  echo "                   Find IP: System Settings → Network"
fi
echo ""
bold "Services:"
echo "  Diagnose issues: ./scripts/doctor.sh"
echo "  Dashboard logs:  tail -f /tmp/gridiron-edge-serve.log"
echo "  Sync logs:       tail -f /tmp/gridiron-edge-sync.log"
echo "  Stop dashboard:  launchctl bootout gui/$(id -u)/com.gridiron-edge.serve"
echo "  Start dashboard: launchctl kickstart gui/$(id -u)/com.gridiron-edge.serve"
echo ""
bold "Access from outside your home (optional):"
echo "  Install Tailscale on Mac mini + phone: https://tailscale.com/download"
echo ""
