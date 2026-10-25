# Allegiance & Influence

Read AGENTS.md and docs/replit-hosting.md. This is an existing game, not a scaffold to regenerate.

- Run: `bash scripts/replit-preview.sh` builds the static Next.js frontend and starts the Python API on 0.0.0.0:3000. One process serves HTML, assets, HTTP, and WebSockets.
- Build: `bash scripts/replit-build.sh`. Publish: `bash scripts/replit-start.sh`.
- Publish as one Reserved VM, never Autoscale or multiple workers. PostgreSQL DATABASE_URL is mandatory in production; SQLite remains the default local/preview option.
- Add the development database through Replit's Database tool and configure a separate production database in Publishing. Schema is created by the app. Do not share databases across active servers.
- Default play is scripted. For real models set GAME_MODEL_CONFIG=config/models.verified-2026-10-24.json and OPENROUTER_API_KEY in Secrets. Keep keys server-side; never commit them or put them in NEXT_PUBLIC variables.
- Preserve artwork, contracts, pure game rules, model profiles, and the existing Python/FastAPI runtime. Do not launch historical backend/htw Firebase code or introduce a second Node server.
- Verification: scripts/agent-verify.sh (offline); TEST_DATABASE_URL pointing to a disposable PostgreSQL database enables backend/tests/test_postgres.py.
