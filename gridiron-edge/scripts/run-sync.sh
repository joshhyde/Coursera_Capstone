#!/usr/bin/env bash
# Wrapper for launchd — loads .env then syncs odds.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
exec "$ROOT/.venv/bin/gridiron" sync
