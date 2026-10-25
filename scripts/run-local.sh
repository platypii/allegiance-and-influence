#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
while (( $# )); do
  case "$1" in
    --models|--key-file)
      if (( $# < 2 )) || [[ -z "$2" || "$2" == --* ]]; then
        printf 'Missing value for %s\n' "$1" >&2
        exit 2
      fi
      if [[ "$1" == --models ]]; then export GAME_MODEL_CONFIG="$2";
      else export OPENROUTER_API_KEY_FILE="$2"; fi
      shift 2 ;;
    --help)
      printf 'Usage: bash scripts/run-local.sh [--models data/models.json] [--key-file data/openrouter.key]\n'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done
if [[ ! -x .venv/bin/python || ! -f frontend/out/index.html ]]; then
  printf 'Run bash scripts/setup.sh first.\n' >&2
  exit 1
fi
exec .venv/bin/python -m uvicorn game.app:create_app --factory --app-dir backend --workers 1 --host "${GAME_HOST:-127.0.0.1}" --port "${GAME_PORT:-8000}"
