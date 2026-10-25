#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -z "${DATABASE_URL:-}" ]]; then
  printf 'Publishing requires DATABASE_URL from a production PostgreSQL database. Local files are not durable on Replit.\n' >&2
  exit 1
fi
export GAME_HOST=0.0.0.0 GAME_PORT="${PORT:-3000}"
exec bash scripts/run-local.sh
