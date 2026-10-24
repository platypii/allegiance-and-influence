#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT
mkdir -p artifacts
unset GAME_MODEL_CONFIG OPENROUTER_API_KEY OPENROUTER_API_KEY_FILE
test_port=8765
test_log=artifacts/e2e-server.log
if [[ "${GAME_TEST_MODE:-scripted}" == model ]]; then
  # Exercise the model-mode interface with a zero-network scripted transport.
  cat > "$test_dir/models.json" <<'JSON'
{"default_profile":"control","profiles":{"control":{"kind":"scripted","model":"scripted-v1"}}}
JSON
  export GAME_MODEL_CONFIG="$test_dir/models.json"
  test_port=8766
  test_log=artifacts/e2e-model-server.log
fi
GAME_SCRIPTED_DELAY_MS=800 GAME_DB="$test_dir/game.sqlite3" GAME_PORT="$test_port" bash scripts/run-local.sh > "$test_log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -rf "$test_dir"' EXIT INT TERM
wait "$server_pid"
