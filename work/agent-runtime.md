# Task: provider-neutral agent runtime

Task: #4. Parent: modernization epic #1, milestone 4. Builds on merged PR #3.

## Goal
Move character replies and recruitment decisions out of the game core into an asynchronous, replaceable provider runtime, preserving the offline game and its artwork.

## Scope lock
`backend/game/**`, `backend/tests/**`, `frontend/app/client.ts`, `frontend/app/panel.tsx`, `frontend/app/page.tsx`, `frontend/tests/**`, `schemas/**`, `tests/fixtures/**`, `scripts/contracts.py`, `scripts/simulate.py`, `scripts/e2e-server.sh`, `docs/**`, `state/PROJECT_STATE.md`, `work/agent-runtime.md`, `README.md`.

## Approach and contracts
A provider receives a frozen observation containing only its character and current conversation. It returns a validated dialogue/recruitment decision plus usage. SQLite tracks pending requests and per-attempt reservations. Completion is accepted only for the matching current request/round/target. Client retries, timeouts, cancellation, and process recovery must never duplicate a message or apply a late decision. Upgrade state views to v2 with explicit v1 compatibility. Keep the existing scripted provider behavior as the conformance baseline.

## Acceptance
- Complete browser and headless matches use the same provider boundary.
- Invalid provider output cannot write arbitrary state or recruit an agent.
- Pending work has visible status; failures permit retry or ending the conversation.
- Timeout, cancellation, bounded retry, concurrency, and restart recovery have tests.
- Per-game call/token/cost reservations are atomic; failed or uncertain attempts do not silently refund a potentially spent budget.
- Record provider/model/prompt identity, attempts, latency, reported usage, and conservative budget charges separately.
- Opponent chat and player keys never enter provider requests or public projections.
- Default verification and local play remain fully offline; no paid model requests.
- Existing games/replays remain readable; original artwork stays intact.

## Non-goals
Live paid-provider evaluation, token streaming, cross-round memory, new gameplay mechanics, public hosting, or distributed scheduling. This increment establishes the runtime and fake-provider conformance before those integrations.

## Evidence
Run the full verification gate, inspect UI captures, and exercise delayed/failing/invalid providers in tests. Document behavioral/contract changes and update project state.

## Implementation notes

The scripted provider now runs through durable jobs and validated results. Game views are v2 with v1 save/replay projection; provider request/result and private attempt report contracts are v1. Browser cancel/retry and fake-provider lifecycle/budget regressions are implemented. Final verification and PR evidence are tracked in project state and the PR.
