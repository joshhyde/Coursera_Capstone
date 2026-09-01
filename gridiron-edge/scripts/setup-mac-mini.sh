#!/usr/bin/env bash
# One-shot Mac mini installer: deps, .env, launchd (dashboard + scheduled sync), LAN access.
#
# Usage:
#   curl -fsSL ... | bash   # or clone repo first (recommended)
#   ./scripts/setup-mac-mini.sh
#   ODDSPAPI_API_KEY=your-key ./scripts/setup-mac-mini.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PORT="${PORT:-8787}"

red() { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
bold() { printf '\033[1m%s\033[0m\n' "$*"; }

if [[ "$(uname)" != "Darwin" ]]; then
  red "This script is for macOS (Mac mini). Run install-mac.sh on other platforms."
  exit 1
fi

bold "==> Gridiron Edge Mac mini setup"
echo "Project: $PROJECT_DIR"

if ! command -v python3 &>/dev/null; then
  red "Python 3 required. Install: brew install python@3.12"
  exit 1
fi

cd "$PROJECT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtualenv..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -e ".[dev]"

mkdir -p "$HOME/.gridiron-edge"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

# API key: env var, first arg, or keep existing .env value
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

# LAN access: bind all interfaces so phones/tablets on same Wi‑Fi can connect
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
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$dest"
  launchctl enable "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl kickstart -k "gui/$(id -u)/$label" 2>/dev/null || true
}

mkdir -p "$LAUNCH_AGENTS"
install_plist "$SCRIPT_DIR/com.gridiron-edge.serve.plist" "com.gridiron-edge.serve"
install_plist "$SCRIPT_DIR/com.gridiron-edge.sync.plist" "com.gridiron-edge.sync"

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
echo "  Dashboard logs:  tail -f /tmp/gridiron-edge-serve.log"
echo "  Sync logs:       tail -f /tmp/gridiron-edge-sync.log"
echo "  Stop dashboard:  launchctl bootout gui/$(id -u)/com.gridiron-edge.serve"
echo "  Start dashboard: launchctl kickstart gui/$(id -u)/com.gridiron-edge.serve"
echo ""
bold "Access from outside your home (optional):"
echo "  Install Tailscale on Mac mini + phone, then use the Tailscale IP:"
echo "  https://tailscale.com/download"
echo ""
