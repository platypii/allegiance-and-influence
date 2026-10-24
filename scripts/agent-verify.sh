#!/usr/bin/env bash
# Same offline gate locally and in CI. Setup is a separate, network-enabled step.
set -uo pipefail
cd "$(dirname "$0")/.."
export NEXT_TELEMETRY_DISABLED=1
unset GAME_MODEL_CONFIG OPENROUTER_API_KEY
failed=()
run_check() {
  local check_name=$1
  shift
  printf '\nCHECK: %s\n' "$check_name"
  "$@"
  local result=$?
  if [[ $result -eq 0 ]]; then
    printf 'PASS: %s (exit %s)\n' "$check_name" "$result"
  else
    printf 'FAIL: %s (exit %s)\n' "$check_name" "$result"
    failed+=("$check_name")
  fi
}
if [[ ! -x .venv/bin/python || ! -x frontend/node_modules/.bin/next || ! -x frontend/node_modules/.bin/playwright ]]; then
  printf 'Missing dependencies. Run bash scripts/setup.sh, then install the Playwright Chromium browser.\n' >&2
  exit 1
fi
run_check 'Contract schemas and failing-fixture proof' .venv/bin/python scripts/contracts.py
run_check 'Python lint' .venv/bin/ruff check --config pyproject.toml backend/game backend/tests scripts
run_check 'Rules, persistence, concurrency and API tests' .venv/bin/python -m pytest -q
run_check 'Original artwork and canonical character data' .venv/bin/python scripts/check-assets.py
run_check 'Frontend build and types' npm --prefix frontend run build
if [[ " ${failed[*]} " != *"Frontend build and types"* ]]; then
  run_check 'Two-player browser workflows' npm --prefix frontend run test:e2e
  run_check 'Browser server error log' .venv/bin/python -c 'from pathlib import Path; paths=list(Path("artifacts").glob("e2e*-server.log")); assert len(paths)>=2, "Server logs missing"; s="\n".join(p.read_text() for p in paths); assert "Traceback" not in s and "ERROR:" not in s, "Server exceptions: inspect artifacts/e2e-server.log"'
fi
run_check 'Patch whitespace' git diff --check
if (( ${#failed[@]} )); then
  printf '\nFAILED CHECKS:\n'
  printf ' - %s\n' "${failed[@]}"
  exit 1
fi
printf '\nPASS: all verification checks\n'
