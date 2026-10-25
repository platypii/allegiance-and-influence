# Import and host on Replit

This repository runs one Python server for the existing interface, HTTP API, WebSockets, and background model jobs. Replit is the first hosting target; local play still uses SQLite without a database service. No Firebase setup is needed.

## Import and preview

1. Open [Replit's GitHub importer](https://replit.com/import) and select `platypii/allegiance-and-influence`. Import the branch containing this change (`codex/replit-import` until merged, then `master`). If the importer only offers the default branch, use the Git pane or Shell to check out the prepared branch before running.
2. Keep the repository's `.replit` configuration. It selects Python 3.12 and Node 22, disables automatic dependency guessing, and maps port 3000. The Run command builds the static frontend and launches the Python server.
3. Click **Run**. The first run installs locked dependencies and builds the frontend; subsequent Runs also rebuild to include source edits. Open Preview in a full browser tab. Default play is a scripted demo and needs no API key.
4. Optionally add a **development PostgreSQL database** through Replit's Database tool. The app uses its `DATABASE_URL` automatically and creates its tables. Without it, preview uses workspace SQLite, which is suitable for trying the game but is not production storage.

Source, assets, and lockfiles come from GitHub. Secrets and this machine's saved games do not. See [Replit's import documentation](https://docs.replit.com/build/import-from-providers).

## Publish a durable playtest

Select **Reserved VM**, one instance/worker. Start with the smallest shared-CPU option offering at least **1 GiB RAM**; remote OpenRouter inference needs no GPU. Increase RAM only if Replit reports memory pressure. The frontend builds separately from runtime. Check the actual estimate in Publishing against your remaining monthly credits: the subscription is not a promise of unlimited hosting, and database usage also consumes credits. [Deployment types](https://docs.replit.com/features/publishing/deployment-types), [usage pricing](https://docs.replit.com/billing/deployment-pricing).

Use these commands (already in `.replit`):

| Setting | Value |
| --- | --- |
| Build | `bash scripts/replit-build.sh` |
| Run | `bash scripts/replit-start.sh` |
| Port | `3000` (binds `0.0.0.0`; honors a platform-provided `PORT`) |
| Health URL | `/api/health` |
| Storage | Production PostgreSQL via `DATABASE_URL` |

Create/select a **production database separate from development** in Replit's Database/Publishing tools. Make its connection string available as `DATABASE_URL` in the published environment. The start command refuses to run without it, because [published filesystems are not durable](https://docs.replit.com/learn/projects-and-artifacts/replit-deployments). Tables initialize automatically; there is no seed/reset command to run. Never point preview at the live production database.

Use a **direct connection or session-mode pooler**, not a transaction-mode pooler. The app keeps one PostgreSQL session and a session advisory lock to enforce one coordinator. For a legacy Neon database, use the direct/unpooled connection string from database settings (a hostname containing `-pooler` is pooled). Preserve the connection's TLS settings. Replit documents [connection details here](https://docs.replit.com/features/data-and-storage/connection-details).

Do not select Autoscale, add Uvicorn workers, or use `--reload` in production. A second process targeting the same schema exits with `This database already has an active game server`. Stop the old deployment before starting its replacement if Replit attempts an overlapping rollout; brief downtime is expected. This protects pending work and WebSocket coordination rather than providing distributed scheduling.

## Enable real models

Add these server environment variables in **Secrets**, and make sure they are included in the published environment:

| Variable | Value |
| --- | --- |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `GAME_MODEL_CONFIG` | `config/models.verified-2026-10-24.json` |

The tracked configuration contains the model IDs and limits tested on 2026-10-24: Haiku as the default character model, Gemini Flash Lite for Churchill, and selectable Luna/Haiku/Gemini/scripted opponents. Edit a tracked copy under `config/` to change profiles, per-character assignments, or budgets; update `GAME_MODEL_CONFIG` to that path. IDs/prices/availability can change: [model setup instructions](model-experiments.md) explain validation. New games pin the configuration; changing it does not silently migrate existing games.

Keep `OPENROUTER_API_KEY_FILE` unset on Replit, unless you deliberately supply a private file: it takes precedence over the environment key. Never use `NEXT_PUBLIC_` variables for credentials. No Replit AI integration is required. OpenRouter charges remain separate from Replit hosting; the shipped configuration caps each game at $1. Public visitors can create games using the configured models. This version has player-seat keys but no account/login or global application spending limit; the OpenRouter key's account budget remains the overall cap.

## Verify the published app

- Open `/api/health`, then start a solo game. If configured, verify the chosen opponent and character model labels.
- Open an invite in a separate browser/device and verify the same session ID and available seat. Use the published HTTPS address, not the development Preview URL.
- Finish a round, retain the player browser tab, restart the deployment, reload, and check that the game/replay persists. Seat credentials are tab-local; losing the tab can lose the seat.
- Restarting during a model call records interruption without silently reissuing the request. Resume/retry from the UI. Unknown charges retain their reservation.

Local tests and CI exercise real PostgreSQL, HTTP/WebSockets, solo/mixed-model play, ownership, rollback, concurrent seat/budget writes, recovery, and production startup. They do **not** prove an account-side Replit import, Nix module resolution, database proxy compatibility, rollout behavior, or publishing succeeds. Complete the checks above in your Replit account before sharing the URL widely.

## Operations and backups

Use Replit's Console/Publishing logs for startup errors. Do not paste Secrets or database URLs into issues. `/api/health` checks the database as well as the app. A lost database session fails closed; restart the deployment after restoring connectivity. No automatic reconnection can accidentally relinquish single-server ownership.

Use the database provider's recovery controls and take a PostgreSQL backup before schema changes. With PostgreSQL client tools matching the server major version or newer, in a private shell where `DATABASE_URL` is already configured:

```bash
mkdir -p artifacts
umask 077
pg_dump --dbname="$DATABASE_URL" --format=custom --file=artifacts/game-backup.dump
```

Download backups from the Replit workspace; the artifact directory is ignored by Git. A database dump includes game transcripts and hashed seat credentials. Restore into a **new empty database**, with the game stopped, then point the app at that database:

```bash
pg_restore --no-owner --no-privileges --dbname="$RESTORE_DATABASE_URL" artifacts/game-backup.dump
```

`RESTORE_DATABASE_URL` must identify the new restore target. Test restoration before relying on backups. Local SQLite saves are not imported automatically into PostgreSQL; this deployment begins with fresh sessions.

## Developer checks

The default `bash scripts/agent-verify.sh` clears database/model environment variables and remains entirely offline after setup. PostgreSQL checks are separate:

```bash
uv sync --locked --extra postgres --python 3.12
# Set TEST_DATABASE_URL to a disposable PostgreSQL database that allows CREATE SCHEMA.
.venv/bin/python -m pytest -q backend/tests/test_postgres.py
```

Each test creates and drops a unique schema. `TEST_DATABASE_URL` is never inferred from `DATABASE_URL`. CI supplies a disposable PostgreSQL 18 service. The optional driver is not installed by local `scripts/setup.sh`; regular local play remains self-contained.
