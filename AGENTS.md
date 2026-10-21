# Working on Allegiance & Influence

Read `state/PROJECT_STATE.md`, `docs/modernization-plan.md`, and the relevant contract before changes. `docs/current-system-map.md` describes the historical Firebase baseline, not the current runtime.

## Workflow

Use Scope, Plan, Execute, Assess, Resolve for substantive changes. The user authorized autonomous execution of the modernization plan on 2026-10-21; routine implementation inside that scope does not require repeated approval. Record new architectural decisions in `docs/decision-log.md` and progress in `state/PROJECT_STATE.md`. Keep future live-model spending and public hosting separate from this offline baseline.

Work from a `codex/` branch. Use a scoped task, explicit acceptance criteria, and evidence. Local task packets live in `work/` and can be mirrored to GitHub. Do not claim a task complete until its checks pass. Do not modify unrelated user work.

## Architecture

- `backend/game/`: current local service, pure game transitions, SQLite store, API contracts.
- `frontend/`: static Next.js interface and original artwork; the Python service serves the build.
- `gameplay/characters.json`: canonical roster shared by both surfaces.
- `backend/htw/`, `backend/scripts/`, and backend Poetry files: historical Firebase experiment, not the current runtime. Never launch it against a live database during verification.
- The server owns scores, phases, target arbitration, and allegiance. Browser commands cannot set those fields.
- Shared contracts need a document, schema, fixtures, and executable validation. Update them together.

## Verification

Install with `bash scripts/setup.sh`. Install browser test support with `cd frontend && npx playwright install chromium` (CI also installs system dependencies). Then run `bash scripts/agent-verify.sh` from the repository root. It requires no cloud credentials, paid APIs, or external services. The default runtime is deliberately scripted; do not present it as model-generated intelligence.

Keep the original artwork intact. For interface changes, run browser tests, inspect their screenshots, and report any intentional visual differences. Tests and screenshots live under `artifacts/` and are ignored by Git; CI uploads them.

## Polling cost

Prefer completion notifications or one tool-side watcher with no model turns between checks. Keep one watcher per job. If model-backed polling is necessary, use only the cheapest available model at its lowest reasoning effort in a dedicated polling-only worker; if it cannot be selected, use tool-side waiting. Return diagnosis and code work to the task owner. Never omit verification to reduce cost.
