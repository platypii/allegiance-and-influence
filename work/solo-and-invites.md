# Scope: session invites and a selectable solo opponent

Issues #8 and #9, under epic #1. Branch `codex/solo-and-invites` is stacked on unmerged PR #7; do not merge its base implicitly.

## Plan

Fix HTTP clipboard failure with an explicit game-ID URL, a visible selectable fallback, and a lobby invite. Add optional solo setup using a server-allowlisted model profile, reserve Blue, and let the model generate up to two recruitment arguments per round. Initial target policy prefers non-Blue characters after Red chooses; it is deterministic, not model strategy. Keep character models independently assigned. Reuse durable jobs and one shared budget for opponent arguments and character replies. Terminal opponent failures end its conversation with a visible reason; no model substitution. Human advances rounds.

Owned paths: backend/game and tests; frontend/app and tests; contracts/schemas/fixtures; scripts/contracts.py; docs, README, state, this packet. Preserve artwork. No public hosting, mobile packaging, ambient-model rewrite, or unrelated gameplay changes.

## Acceptance and assessment

- Copied/fallback invite opens the same session in a separate browser over HTTP.
- Solo human can finish multiple rounds; selected model is pinned and visible; Blue cannot be claimed externally.
- Opponent requests cannot see human dialogue; valid model arguments go through normal character replies and scoring. All calls share configured budgets and timeout/concurrency controls.
- Failure, restart, invalid model choice, changed provider, duplicate actions, and stale results remain bounded and cannot strand the round.
- Versioned contracts and historical projections, backend/browser coverage, inspected captures, original asset hashes, full offline verifier, and a bounded live solo smoke check.

Record measured evidence after checks pass. Use repo issues for actionable playtest bugs/features going forward.

## Resolve: evidence

The full verifier passed with 90 backend tests and 5 browser workflows. Includes mixed-model routing, rejected unknown profiles, reserved Blue seat, two-round solo completion, shared budget exhaustion, timeout/provider failures, interrupted restart, observation privacy, stale completion, atomic argument-to-character handoff, identity pinning, v3 migration, invite fallback/copy, mobile setup, and reload. All 58 artwork files remain unchanged; captures 09–13 were inspected. The first solo browser assertion incorrectly expected Blue 1 rather than the existing ambient propagation's Blue 3; corrected the assertion without changing game rules.

The updated service on the Tailscale address completed one actual solo round against Luna. Two Luna arguments and two Haiku character replies recruited Einstein; the human's Gemini character reply declined recruitment. Five calls succeeded for $0.000857, final Red 0 / Blue 1, no JavaScript or server errors. The same real HTTP browser environment exercised unavailable clipboard access, copied the displayed session URL, and joined it from another independent context. No additional inference was needed for invite verification.

Ignored local evidence: `artifacts/live-solo-browser.json`, `artifacts/live-solo-accounting.json`, `artifacts/screenshots/09-*` through `13-*`, and a pre-update SQLite backup. The actual match is in `data/model-game.sqlite3`; credentials and player keys were not exported. Fixed target policy/two-argument cap, private opponent dialogue, and deterministic ambient pairs remain explicit limitations.
