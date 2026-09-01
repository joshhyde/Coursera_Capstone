#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Gridiron Edge Mac mini setup"

if ! command -v python3 &>/dev/null; then
  echo "Python 3 is required. Install via Homebrew: brew install python@3.12"
  exit 1
fi

cd "$PROJECT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -e ".[dev]"

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "Created .env — add your ODDSPAPI_API_KEY before running."
fi

mkdir -p ~/.gridiron-edge

echo ""
echo "Setup complete. Next steps:"
echo "  1. Edit $PROJECT_DIR/.env with your API key"
echo "  2. source .venv/bin/activate && gridiron sync"
echo "  3. gridiron serve   # dashboard at http://127.0.0.1:8787"
echo ""
echo "Optional: install launchd scheduler:"
echo "  cp scripts/com.gridiron-edge.sync.plist ~/Library/LaunchAgents/"
echo "  launchctl load ~/Library/LaunchAgents/com.gridiron-edge.sync.plist"
