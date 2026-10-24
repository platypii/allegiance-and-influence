# Game protocol v3

Purpose: give browsers and headless experiments the same authoritative game lifecycle, with saved state and replay. The initial rules version is `scripted-v1`; it is a deterministic infrastructure baseline, not an approximation of a modern LLM's persuasion judgment.

## State and authority

The server owns each game. A game has an unguessable ID, monotonically increasing version, configuration, participants, phase, one-based round number, characters, conversations, pairings, round history, scores, and winner. New state carries `schema_version: "3"`. Scripted games use `rules_version: "scripted-v1"` and `mode: "scripted"`; configured character models use `rules_version: "persuasion-v1"` and `mode: "model"`. Rules still own recruitment and scoring.

Lifecycle: `lobby → selecting → conversing → round_complete → selecting … → finished`. The last round moves directly from conversing to finished. Both seats must be claimed before selecting; both distinct targets must be selected before conversing. The first accepted selection owns a target for that round. Either player may advance a completed round; duplicates/stale versions cannot advance it twice.

Clients send `select`, `message`, `done`, `advance`, `retry`, or `cancel`. Each command carries a unique `command_id` and `expected_version`; the authenticated seat is inferred from its player key. Extra fields are rejected. A duplicate ID with the same actor and exact payload returns the current state without applying twice. Reusing an ID for a different payload or actor fails. A new stale-version command fails with `stale_version`; the client refreshes and asks the user to retry. A transport failure may retry the exact command once with the same ID.

The command and view schemas live in `schemas/command-v2.schema.json` and `schemas/game-view-v3.schema.json`. They are generated from runtime validation models. `scripts/contracts.py` checks drift and valid/invalid fixtures. Unknown fields fail, including attempted client-written scores or allegiance.

## Scripted rules

- Roster: 2–23 characters selected with the configured seed; 1–20 rounds.
- Human conversations: at most five nonblank messages of at most 2,000 characters. The scripted response promises recruitment after the second message. Recruitment is committed when both conversations finish.
- Empty conversations preserve allegiance. The scripted provider proposes recruitment after two messages; only an accepted provider decision affects round resolution. A failed/cancelled reply cannot itself recruit. These are explicit demo rules, not legacy behavior parity or final gameplay design.
- Remaining agents are shuffled deterministically for the round. Each participates in at most one pair; one character rests if the remaining count is odd.
- A faction member persuades a neutral paired character. Opposing factions and two neutral characters keep their current sides. Pair outcomes resolve against the same starting sides.
- Scores count characters only. Winner and ties are computed by the server after final-round effects; no hard-coded round count in the browser.
- Round completion, scoring, history, and final outcome are persisted together. Pending reply requests are tracked separately; a player must wait, cancel, or handle a terminal failure before ending their conversation. See [agent runtime contract](agent-runtime-contract.md).

## HTTP and live updates

- `POST /api/games`: create from agent count, round count, and seed; defaults 6/3/32.
- `GET /api/games/{id}`: snapshot, optionally authenticated.
- `POST /api/games/{id}/join`: claim `player_red` or `player_blue` using a client-generated bearer key. Retrying the same seat/key is idempotent.
- `POST /api/games/{id}/commands`: validated authenticated command.
- `GET /api/games/{id}/replay`: authenticated, ordered snapshot frames filtered for the requesting seat.
- `WS /api/games/{id}/live`: first frame supplies authorization, then receive current snapshot and subsequent updates. No credentials in query strings. A missing key creates a spectator view.
- `GET /api/games/{id}/runtime`: authenticated provider identity, policy, and that seat's attempt/usage report.
- `GET /api/health`: local service health.

Domain failures return an HTTP status and `{ "error": { "code": "…", "message": "…" } }`. Malformed request bodies return framework validation errors (422). A failed command does not increment the version or append an event. Browser-origin HTTP and WebSocket traffic must match the server address.

The WebSocket sends bounded full snapshots: a slow reader may skip intermediate updates and converges to the latest version; replay retains committed transitions. Reconnect starts with the current snapshot. The browser rejects snapshots older than its displayed version. This is deliberately one server process; multiple workers would need shared notification and match ownership coordination.

## Persistence, identity, and replay

SQLite contains snapshots, seat key hashes, and ordered accepted-command events with their resulting state. Snapshot and event commit in one transaction. Transactions do not await model calls. Original player keys live in each tab's session storage and are never put in snapshots/events/replay. Losing a tab's key has no recovery flow yet; creating another game is the current fallback.

Other players and spectators see selected targets, completion flags, scores, and recaps, but not another seat's dialogue. Player replay follows that same visibility rule. Locally stored transcripts are plaintext on the host and retained until the operator removes the local save; no cloud sync or automatic retention process exists.

Replay is playback of committed snapshots, so it does not need inference. It is not yet an event-only state reconstruction engine or a reproducibility guarantee for future live providers. Seeded simulation is deterministic given the same rules/content and commands. Future breaking state/command changes must version their contract and supply migration or explicit compatibility handling.

## Verification and boundaries

The API tests exercise complete games, final outcomes, collisions, idempotence, stale commands, unauthorized access, privacy, WebSocket reconnects, concurrent writes, and state survival across app recreation. Browser tests drive two independent clients, reload, replay, and a narrow viewport while rejecting external requests. Original graphic files are hash-checked against commit `8247a6776e3ccab6945419ace142531d2cb431a5`.

OpenRouter character models and controlled paired experiments are described in [model-experiments.md](model-experiments.md). Streaming model tokens, richer memory, public accounts, seat takeover, and multi-server hosting remain future work. Artwork is preserved; browser captures establish a new local baseline, not pixel-perfect proof of the unrun historical Firebase deployment.

## Historical compatibility

The service reads v1/v2 saves and replay frames through a v3 projection without changing their recorded versions or inventing provider calls. Historical scripted recruitment is derived from the existing messages. Subsequent writes use v3. Historical schemas remain archived; the current game view validates v3. Saved scripted games are not silently switched to model mode.
