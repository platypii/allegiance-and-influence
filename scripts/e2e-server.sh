#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT
mkdir -p artifacts
GAME_SCRIPTED_DELAY_MS=800 GAME_DB="$test_dir/game.sqlite3" GAME_PORT=8765 bash scripts/run-local.sh > artifacts/e2e-server.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -rf "$test_dir"' EXIT INT TERM
wait "$server_pid"
