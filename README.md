# Allegiance & Influence

Recruit historical characters, build a faction, and watch influence spread across the room. The game is being modernized into a local multiplayer game and a repeatable AI experiment test bed while preserving its original artwork.

The current baseline runs **entirely locally with scripted characters**. No Firebase project, API key, Docker, or separate database server is needed. It supports two human players, saved games, reconnects, and replay. Live generative models are a subsequent milestone.

## Run locally

Prerequisites: Python 3.12 through [uv](https://docs.astral.sh/uv/) and Node.js 22 or later with npm. Dependency installation needs an internet connection; running the installed game does not.

From this repository's root:

```bash
bash scripts/setup.sh
bash scripts/run-local.sh
```

Open **http://127.0.0.1:8000**. Create a game, choose Red, then open the game address in another independent tab or browser and choose Blue. The two tabs keep separate player keys. Reuse each player's existing tab to resume after a server restart; reload preserves the key. Closing a tab may discard its key: durable account recovery is not part of this baseline.

Both players choose different characters. In this scripted demo, sending two messages recruits the character when the round resolves; up to five messages are allowed. Click **Done talking** on both sides, review the recap, and click **Next round**. The final result counts recruited characters only and supports ties. **Review replay** steps through committed states without making model calls.

After setup, one Python process serves the interface, API, WebSockets, and SQLite storage. Node is needed to rebuild the interface, not to serve the built game.

```bash
# Optional: allow devices on your trusted LAN to connect to this machine's IP.
GAME_HOST=0.0.0.0 GAME_PORT=8000 bash scripts/run-local.sh

# Optional: separate save location.
GAME_DB=/absolute/path/to/game.sqlite3 bash scripts/run-local.sh
```

The default save is `data/game.sqlite3`. Startup never resets games. To back it up, stop the server and copy the data directory, including any SQLite sidecar files. This is a single-server local/LAN baseline; public internet hosting and account management remain future work.

## Develop and verify

```bash
# Once, install the test browser after setup.
cd frontend
npx playwright install chromium
cd ..

# Same complete gate locally and in CI.
bash scripts/agent-verify.sh

# Rebuild frontend after interface edits, then reload your browser.
npm --prefix frontend run build

# Optional: API-only development with reload.
.venv/bin/python -m uvicorn game.app:create_app --factory --app-dir backend --reload
```

The verifier checks contract fixtures (including deliberate failures), Python rules/API/concurrency/recovery tests, original asset hashes, static build/typechecking, two-player browser workflows, and server errors. Browser tests create an isolated temporary database and write screenshots/traces to `artifacts/`. They do not touch your saved games.

## Headless baseline

```bash
.venv/bin/python scripts/simulate.py --seed 32 --rounds 3 --agents 6 --output artifacts/replay.json
```

This drives the same game transitions and persistence boundary with scripted players. The optional JSON contains a manifest and public replay frames; private conversations and player keys are excluded. This is a smoke experiment, not a model benchmark.

## Architecture and roadmap

- [Modernization plan](docs/modernization-plan.md)
- [Current implementation and progress](state/PROJECT_STATE.md)
- [Game protocol and rules](docs/game-contract.md)
- [Architecture decisions](docs/decision-log.md)
- [Historical system map](docs/current-system-map.md)
- [Agent working instructions](AGENTS.md)

The original Firebase/LangGraph implementation remains in `backend/htw/` and `backend/scripts/` for reference. Its Poetry environment is historical and is not installed by the new root setup. Its launcher clears its configured database; it is not the supported local entry point.

Licensed under [MIT](LICENSE).
