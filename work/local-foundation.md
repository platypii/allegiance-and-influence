# Task: self-contained local foundation

Parent: [modernization epic #1](https://github.com/platypii/allegiance-and-influence/issues/1), milestones 1–3 (first vertical slice).
Task: [local foundation #2](https://github.com/platypii/allegiance-and-influence/issues/2).
Authorization: user requested autonomous execution on 2026-10-21.

## Goal

Replace the default external-service launch with a complete, locally saved two-player match that preserves the existing artwork and provides a verifiable foundation for model integration.

## Scope

Owned paths: `backend/game/**`, `backend/tests/**`, `frontend/**` excluding original graphic bytes, `scripts/**`, `schemas/**`, `tests/fixtures/**`, `.github/**`, `.gitignore`, `.python-version`, `pyproject.toml`, `uv.lock`, `README.md`, `AGENTS.md`, `docs/**`, `state/**`, `work/**`.

Inputs: historical source at 8247a67, original assets, canonical character JSON, modernization plan, user's local-operation preference.

Non-goals: paid inference, final gameplay balance, public deployment, accounts, replacing artwork, or deleting historical source.

## Acceptance

- One command runs the installed app without cloud keys/services.
- Two browser clients finish a configurable multi-round match; scoring excludes humans and ties work.
- Seats and game state survive server restart with the existing client key.
- Commands are validated, serialized, idempotent, and game-scoped; private chats do not leak to opponents.
- Recorded states replay without inference.
- Original graphic bytes remain intact; new screenshots are visually inspected.
- One gate runs contracts, API/rules tests, asset checks, static build/types, browser workflows, and server-log checks.

## Test plan and evidence

Run `bash scripts/agent-verify.sh`. Inspect `artifacts/screenshots/`. Run `scripts/simulate.py` for a headless smoke match. Record exact results in `state/PROJECT_STATE.md`; do not equate scripted rules with live model acceptance.

## Follow-on tasks

1. Introduce a provider-neutral agent runtime with fake-provider conformance tests, cancellation, model decisions, and budget accounting.
2. Evaluate current live models against controlled scenarios with an explicit spend ceiling.
3. Add durable agent memory and repeatable policy/model comparisons.
4. Playtest baseline pacing and meaningful choices before extending mechanics.
