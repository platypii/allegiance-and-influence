# Agent runtime contract v2

The runtime owns provider execution; game rules own legal transitions and scoring. The default `scripted` / `scripted-v1` provider preserves the local demo's two-message recruitment behavior. Test providers exercise the same boundary. Hosted OpenRouter adapters and per-character routing are optional; see [model experiments](model-experiments.md).

## Provider boundary

`AgentRequest` is a frozen observation for one character's reply: request/game IDs, round, that character's description/attributes/allegiance, the opponent's seat/side and optional public character persona, and that conversation's messages. It contains no other player's dialogue, authentication keys, global game state, or private replay. Providers receive a deep copy.

`ProviderResult` contains only a schema version, `decision` (dialogue and boolean `join_opponent`), `usage` (input tokens, output tokens, integer micro-USD cost), and an optional transport receipt (requested/actual model, generation ID, and upstream provider). One dollar equals 1,000,000 micro-USD. Empty/blank dialogue, oversized dialogue, extra fields, coerced types, and negative usage fail validation. The output cannot name a winner, set a score, choose another target, or write a team directly.

The authoritative game commits the accepted dialogue and decision only if game phase, round, character, request ID, and pending status still match. Allegiance changes occur at round resolution, not on token generation. Ambient AI-pair interactions remain the deterministic existing rules; moving those conversations into the runtime is future work.

Initial greetings are fixed presentation text. Each accepted human message creates a reply request. `retry` creates a new request for the same observation without appending another human message. `cancel` terminates the current request. New messages and `done` are rejected while a reply is pending. After a terminal failure, the player may retry, send another message, or finish.

## Durable lifecycle and restart

SQLite atomically commits the human command, new game snapshot, and queued job. The job stores its request, owning seat, immutable game provider identity and policy, and status. Provider I/O occurs outside all database transactions.

Jobs move from queued to running and then succeeded, failed, cancelled, or interrupted. A stale completion is discarded. The game's conversation exposes pending/succeeded/failed/cancelled/interrupted and a safe error code to its owner. Opponents and spectators receive no work details or recruitment decision.

Each successful reply or failure gets its own snapshot/event version. Client command idempotence still applies; resubmitting an accepted command does not launch another provider call. Cancellation commits before the task is cancelled. Late responses are ignored even if the adapter suppresses cancellation. Retry uses a different request identity, so an old completion cannot satisfy it.

On startup, queued/running jobs become interrupted and potentially started attempts retain their reservations. Nothing is automatically reissued: a process can crash after the remote service performed work but before local completion. A user may explicitly retry or finish. This provides at-most-once application of a result, not an exactly-once guarantee for a future remote provider's execution or billing.

## Concurrency, timeout, and retry

A process-wide semaphore bounds provider calls. Queue capacity bounds active request drivers. Slow/noncooperative calls retain their concurrency slot until they actually finish; a timed-out result never re-enters the game. Adapters must honor cancellation and their declared output/usage bounds. Shutdown gives cancelled provider tasks a bounded grace interval; this is not OS-level isolation of untrusted Python.

Each attempt has a deadline that includes waiting for a concurrency slot. Only an explicitly classified `RetryableProviderError` triggers automatic retry, bounded by `max_attempts` and a fresh budget reservation. Invalid output, arbitrary errors, timeout, changed provider identity, and cancellation do not automatically retry. Raw exception messages are not shown to players or stored in their game events.

## Accounting and budgets

New games pin provider/router identity, per-character assignments, prompt/settings fingerprints, and runtime policy at creation. Each job stores its selected model identity and token/cost ceilings. Legacy games retain existing metadata or pin it on first use. A changed provider identity fails explicitly instead of silently continuing the same game with a new model. Existing v1 games pin this metadata when they first use the new runtime.

Before an attempt begins, one SQLite transaction checks the cumulative call/token/cost limits and reserves the declared worst-case token/cost amounts. Concurrent seats share the same game budget. No slot acquisition means no started call or reservation. All started attempts count, including retries and cancellations.

A validated successful response records reported usage and releases unused reservation. Failed, timed-out, cancelled, or interrupted attempts retain the conservative charge; unknown usage is `null`, not fabricated zero. Reported usage and budget charges are separate fields. If an adapter reports usage above its declared bound, record that usage, charge at least the reported amount, reject the decision, and block further calls for that game. A reservation is an application guard based on a trustworthy adapter's bound, not a guarantee against an external provider violating its billing contract.

Defaults: four concurrent calls, 64 active request drivers, ten-second attempt deadline, at most two attempts, 200 started calls per game, 200,000 budget tokens, and **zero allowed cost**. The scripted adapter declares/reports zero tokens and cost. A costed adapter must be configured with an explicit budget and enforce its request/output limits. Tests supply costed fake adapters without network calls.

Each attempt records request identity, status, latency where known, reported usage where known, and charged tokens/cost. Interrupted attempts may have unknown latency. `GET /api/games/{id}/runtime` requires the player's key and returns only that seat's attempts plus the pinned provider/policy. It excludes prompts, dialogue, credentials, and the other seat's attempt history. The local database remains the complete operator record.

## Contracts and verification

- `schemas/agent-request-v2.schema.json`
- `schemas/agent-result-v2.schema.json`
- `schemas/runtime-report-v2.schema.json`
- `schemas/command-v2.schema.json`, `schemas/game-view-v3.schema.json`
- Positive/negative contract fixtures under `tests/fixtures/`; validation through `scripts/contracts.py` and the shared verifier.

Runtime tests cover scripted compatibility, observation privacy, malformed/blank decisions, arbitrary errors, transient retry, budget exhaustion, overshoot, cancellation before/during execution, late responses, capacity, shared concurrency, interrupted recovery, provider mismatch, and legacy snapshot/replay reads. Browser tests exercise waiting/cancel/retry through the real local service.

## Compatibility

Game view v2 adds `join_opponent` and `work` to conversations. Stored v1 snapshots remain untouched until the next committed transition; on read, the adapter derives the previous scripted decision from historical human-message counts and sets work to null. Replay projects those old frames into v3 without inventing model attempts or changing their event versions. Archived v1 schemas remain in the repository.

Clients must understand game view v3; after updating the server, rebuild and reload the static interface. Provider protocol version remains independent of game-view version. Unknown future formats require an explicit migration, not guessed defaults.

Current agent request/result v2 adds optional opponent character and provider receipt fields while accepting legacy v1 payloads. Runtime report v2 includes each attempt’s selected identity and receipt; existing rows have null metadata when none was recorded. Game view v3 exposes model mode. New routing tables/columns are additive migrations.
