#!/usr/bin/env bash
set -euo pipefail

# Repository root is the directory that contains the .cursor folder.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$REPO_ROOT/gridiron-edge"

# Ubuntu's system python does not bundle the venv/ensurepip module. Install it
# once so `python3 -m venv` works. Safe to re-run (apt is idempotent).
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv
fi

cd "$APP_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]"

# Provide a local .env so the app runs with sane defaults out of the box.
# Add ODDSPAPI_API_KEY here to enable live `gridiron sync`.
if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "gridiron-edge environment ready. Activate with: source gridiron-edge/.venv/bin/activate"
