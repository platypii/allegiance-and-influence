#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Rebuild on Run so source edits and lockfile changes are reflected in Preview.
bash scripts/replit-build.sh
if [[ -z "${DATABASE_URL:-}" ]]; then
  printf 'Preview uses local SQLite. Add a development PostgreSQL database to test hosted storage.\n'
fi
export GAME_HOST=0.0.0.0 GAME_PORT="${PORT:-3000}"
exec bash scripts/run-local.sh
