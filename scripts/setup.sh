#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --locked --python 3.12
npm --prefix frontend ci --no-fund
NEXT_TELEMETRY_DISABLED=1 npm --prefix frontend run build
printf '\nReady. Run: bash scripts/run-local.sh\n'
