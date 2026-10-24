# Project state

Updated 2026-10-24. User authorized modernization, approved prior merges, and selected OpenRouter for hosted models with different models per character.

## Milestones

- [PR #3](https://github.com/platypii/allegiance-and-influence/pull/3), local foundation, merged as `d0aff12`: authoritative game rules, SQLite, local multiplayer/replay, original art, and the software factory.
- [PR #5](https://github.com/platypii/allegiance-and-influence/pull/5), provider-neutral runtime, merged as `03b2a49`: durable asynchronous replies, bounded execution, cancellation/retry, recovery, budgets, and offline conformance.
- Current increment: branch `codex/model-conversations`, [task #6](https://github.com/platypii/allegiance-and-influence/issues/6), under [epic #1](https://github.com/platypii/allegiance-and-influence/issues/1). Scope: `work/model-conversations.md`.

## Implemented in this increment

- Optional hosted OpenRouter adapter, without vendor-specific SDK coupling. Default local play remains scripted and offline.
- Model profiles separate from roster personas. Character UID assignments plus a default allow mixed models and scripted controls in one game. Configurations are pinned when a game is created; each job records and reserves its selected model's limits.
- Versioned persona prompt using existing descriptions/attributes, own conversation history, and optional public opponent persona. No keys, assignments, or unrelated dialogue enter model observations.
- Bounded asynchronous HTTP, strict local decisions, native structured output or explicit prompt-JSON mode, no model fallback, optional upstream pin, recorded generation/model/provider receipts, actual usage/cost, and conservative error accounting.
- Paired character experiment relays replies through the existing store/runtime/round rules and one shared budget. Supports swapping model assignments and reversing turn order; exports transcripts, decisions, configuration/hashes, attempt usage/latency, final state, and replay. Failed turns are labelled, never presented as successful persuasion evidence.
- Game view v3, agent request/result v2, runtime report v2, and configuration/scenario/report v1 schemas with fixtures/validation. Old game snapshots and attempt tables migrate without inventing metadata or converting scripted saves to model mode.
- Setup helper creates the editable model file, reads the public model catalog, checks assignments/budgets, and accepts hidden terminal key entry into an owner-only file. Explicit key-file options are supported by the launcher and experiment runner; existing files are never overwritten.
- Browser text distinguishes model mode from the scripted two-message demo. All 58 artwork files remain unchanged.

## Verification evidence

The complete local `bash scripts/agent-verify.sh` gate passed: **79 backend tests**, **3 browser workflows**, schema/fixture validation, Python lint, frontend build/typechecking, original artwork hashes, clean server logs, and patch whitespace. New tests exercise real adapter serialization/parsing through mock HTTP, two different models exchanging four replies, shared selected-model budgets, pinned routing, malformed/incomplete responses, usage/identity validation, and timeout cancellation. Browser model mode uses a scripted fixture transport, not live inference.

Model-mode and welcome captures were inspected. The scripted pair control completed four turns with four attempts and zero charges. `artifacts/pair-mock-report.json` is explicitly labelled `mock-http`. Other ignored evidence: `artifacts/screenshots/`, `artifacts/browser-tests/`, `artifacts/e2e*-server.log`, and paired run output directories.

**No live OpenRouter request was made.** No `OPENROUTER_API_KEY` was available. Current checks establish protocol, accounting, and lifecycle behavior; model availability, latency, personality quality, and persuasion effectiveness remain unmeasured. Hosted CI evidence belongs to the PR and is separate from the local gate.

## Known limits

- Per-character hosted configuration is an operator JSON file, not a browser model picker. A changed routing configuration needs a new game (or restoration of the original configuration to continue an old one).
- The paired experiment is a controlled two-character conversation using synthetic seats. Ambient AI interactions on the multiplayer board and initial greetings remain deterministic.
- No streaming, cross-round memory, local generative adapter, or tournament/statistical comparison runner yet.
- Input admission uses a conservative byte allowance, not exact tokenization for every remote model. Reported bound overruns reject the decision and block further game calls. Price/usage guards rely on the remote service's reported contract; budgets are per game, not across an account. BYOK is unsupported.
- Exactly-once remote inference/billing is not promised. Unknown or failed attempts retain reservations; remote cancellation may still incur charges.
- Single server process; no public accounts, seat recovery, or distributed scheduling. Old browser tabs must reload after updating the service.

## Next work

The local editable `data/models.json` has been initialized with placeholders. Configure the private key using `scripts/model_setup.py key`, then choose concrete model IDs, price ceilings, and a bounded spend policy. Run the paired scenario, swap models between personas, reverse order, and inspect actual transcripts/latency/cost before choosing candidates. The commands are in `docs/model-experiments.md`.

Then add repeated comparisons and broader scenarios, integrate model-driven ambient conversations, and move into human playtesting and small gameplay changes. The offline gate remains mandatory throughout.

Client direction: web app now; possible iPhone/Android clients later should reuse the hosted game API. Credentials and model options stay server-side. Mobile packaging remains undecided until gameplay is established.
