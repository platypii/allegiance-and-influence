#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Use Replit's Python module, including its Nix library environment. Pin uv so
# an older preinstalled package manager cannot reinterpret the committed lock.
python3 -m venv .replit-tools
.replit-tools/bin/python -m pip install --disable-pip-version-check --quiet 'uv==0.12.10'
.replit-tools/bin/uv sync --locked --extra postgres --python "$(command -v python3)"
npm --prefix frontend ci --no-fund
NEXT_TELEMETRY_DISABLED=1 npm --prefix frontend run build
