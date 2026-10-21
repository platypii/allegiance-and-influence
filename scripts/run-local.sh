#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python || ! -f frontend/out/index.html ]]; then
  printf 'Run bash scripts/setup.sh first.\n' >&2
  exit 1
fi
exec .venv/bin/python -m uvicorn game.app:create_app --factory --app-dir backend --host "${GAME_HOST:-127.0.0.1}" --port "${GAME_PORT:-8000}"
