# Project state

Updated 2026-10-24. User authorized modernization and merging all open PRs, and selected OpenRouter for hosted models with different models per character.

## Replit hosting preparation

Issue [#11](https://github.com/platypii/allegiance-and-influence/issues/11), branch `codex/replit-import`, task packet `work/replit-import.md`. The user chose Replit instead of proceeding with DigitalOcean. The implementation adds GitHub import/Run/build/publish configuration and optional PostgreSQL persistence, while keeping local SQLite and all artwork. Single-server ownership is enforced; production requires a separate PostgreSQL database with a direct/session connection. OpenRouter configuration remains explicit and keys stay in Secrets. See [the import/runbook](../docs/replit-hosting.md). Local verification passed: 92 offline backend tests, 5 browser workflows, 19 real PostgreSQL cases, original assets, and a fresh source-only build. CI adds its own PostgreSQL service. No Replit app has been provisioned or published; [PR #12](https://github.com/platypii/allegiance-and-influence/pull/12) merged into `master` as `2663df9` after user approval.

## Design system and mobile readability

Issues [#13](https://github.com/platypii/allegiance-and-influence/issues/13) and [#15](https://github.com/platypii/allegiance-and-influence/issues/15), branch `codex/game-design-system`, [PR #14](https://github.com/platypii/allegiance-and-influence/pull/14), task `work/game-design-system.md`. Shared tokens, `/design-system/`, responsive setup/board/results, and a native conversation dialog establish the visual system. Following user review, the board again animates continuously with wandering, repulsion, faction gravity and pair attraction; full portrait/label bounds prevent collisions. Pointer/focus stability, a pause control and reduced-motion support preserve reliable targeting. Locally bundled Lora renders dialogue and composer text at 18px and supplies the headings. The desktop conversation backdrop leaves the moving board visible.

The full offline verifier passed with 92 backend tests, 11 browser workflows, 3 physics simulations, build/types, contracts, and all 58 original artwork hashes. Browser glyph inspection confirms actual custom Lora rendering. Motion checks cover crowded mobile targets, pause/focus/reduced-motion behavior, and continued movement after a simulated minute. Inspected final desktop/mobile dialogue and board captures. Original assets and game rules remain intact. PR #14 awaits user review; actual device keyboards/screen readers and publishing remain playtest steps.

## Milestones

- [PR #3](https://github.com/platypii/allegiance-and-influence/pull/3), local foundation, merged as `d0aff12`: authoritative game rules, SQLite, local multiplayer/replay, original art, and the software factory.
- [PR #5](https://github.com/platypii/allegiance-and-influence/pull/5), provider-neutral runtime, merged as `03b2a49`: durable asynchronous replies, bounded execution, cancellation/retry, recovery, budgets, and offline conformance.
- [PR #7](https://github.com/platypii/allegiance-and-influence/pull/7), OpenRouter increment, merged as `5fa039e`: [task #6](https://github.com/platypii/allegiance-and-influence/issues/6), under [epic #1](https://github.com/platypii/allegiance-and-influence/issues/1). Scope: `work/model-conversations.md`.

- [PR #10](https://github.com/platypii/allegiance-and-influence/pull/10), solo play and invites, merged as `0bc0fa1`, closes issues [#8](https://github.com/platypii/allegiance-and-influence/issues/8) and [#9](https://github.com/platypii/allegiance-and-influence/issues/9). Merged after PR #7 with explicit user approval; scope: `work/solo-and-invites.md`. Both increments are on the default branch, `master` (this repository has no `main` branch). Issues #6, #8, and #9 are closed; epic #1 remains open.

## Solo and invites: implemented and verified

- Single player is the default setup. Select a server-configured opponent profile; starting auto-joins Red and reserves Blue. Two-human play remains available.
- Blue's selected model writes up to two adaptive recruitment arguments per round. A deterministic policy chooses a distinct target after Red, preferring characters not already Blue. Character responses retain their independent model assignments. Only character decisions recruit; the opponent cannot set allegiance or scores.
- Argument and character jobs share durable storage, bounded execution, immutable route identities, and one game budget. Terminal failure or restart ends the affected Blue turn with a visible reason, allowing the human to finish. Dialogue stays private; safe opponent status/model is visible.
- Invite URLs use the authoritative session ID. HTTP clipboard failure now shows/selects the complete URL for manual copying, and the lobby always offers a session link.
- Current contracts: game view v4, agent request v3, pair report v2, create-game v2, opponent-options v1. Historical schemas remain archived and multiplayer saves project without becoming solo.
- Full offline gate passed: **90 backend tests, 5 browser workflows**, schemas/fixtures, lint, build/types, all **58 artwork hashes**, clean server logs, whitespace. Inspected invite fallback, mobile solo setup, and completed-game captures.
- Actual Tailscale HTTP test joined two browsers through the same invite and completed a one-round solo game against `openai/gpt-6-luna`. All **5 live calls succeeded**, recorded cost **$0.000857**; Blue recruited Einstein and won 1–0. No browser errors. This is end-to-end evidence, not a ranking or fairness study.
- The running model app was restarted on port 8001 after backing up its SQLite database. Tailscale forwarding remains active at `http://100.116.186.44:8001`; reload the browser for the new setup. Both app and transient forwarding need restarting after reboot.

## OpenRouter increment

- Optional hosted OpenRouter adapter, without vendor-specific SDK coupling. Default local play remains scripted and offline.
- Model profiles separate from roster personas. Character UID assignments plus a default allow mixed models and scripted controls in one game. Configurations are pinned when a game is created; each job records and reserves its selected model's limits.
- Versioned persona prompt using existing descriptions/attributes, own conversation history, and optional public opponent persona. No keys, assignments, or unrelated dialogue enter model observations.
- Bounded asynchronous HTTP, strict local decisions, native structured output or explicit prompt-JSON mode, no model fallback, optional upstream pin, recorded generation/model/provider receipts, actual usage/cost, and conservative error accounting.
- Paired character experiment relays replies through the existing store/runtime/round rules and one shared budget. Supports swapping model assignments and reversing turn order; exports transcripts, decisions, configuration/hashes, attempt usage/latency, final state, and replay. Failed turns are labelled, never presented as successful persuasion evidence.
- Game view v3, agent request/result v2, runtime report v2, and configuration/scenario/report v1 schemas with fixtures/validation. Old game snapshots and attempt tables migrate without inventing metadata or converting scripted saves to model mode.
- Setup helper creates the editable model file, reads the public model catalog, checks assignments/budgets, and accepts hidden terminal key entry into an owner-only file. Explicit key-file options are supported by the launcher and experiment runner; existing files are never overwritten.
- Browser text distinguishes model mode from the scripted two-message demo. All 58 artwork files remain unchanged.

## Earlier OpenRouter verification evidence

The complete local `bash scripts/agent-verify.sh` gate passed: **79 backend tests**, **3 browser workflows**, schema/fixture validation, Python lint, frontend build/typechecking, original artwork hashes, clean server logs, and patch whitespace. New tests exercise real adapter serialization/parsing through mock HTTP, two different models exchanging four replies, shared selected-model budgets, pinned routing, malformed/incomplete responses, usage/identity validation, and timeout cancellation. Browser model mode uses a scripted fixture transport, not live inference.

Model-mode and welcome captures were inspected. The scripted pair control completed four turns with four attempts and zero charges. `artifacts/pair-mock-report.json` is explicitly labelled `mock-http`. Other ignored evidence: `artifacts/screenshots/`, `artifacts/browser-tests/`, `artifacts/e2e*-server.log`, and paired run output directories.

After the user configured a key and confirmed its spending cap, five live paired runs completed **18 valid replies**, followed by **one successful live browser reply**. The recorded total was **$0.004381**. All requested model IDs matched the receipts; no repairs or retries were needed. All paired decisions declined recruitment. This validates compatibility and the end-to-end path, not model superiority or general persuasion quality. See [dated results and limitations](../docs/live-validation-2026-10-24.md). The full offline gate passed again after synchronizing browser selection assertions with WebSocket updates. Hosted CI evidence belongs to [PR #7](https://github.com/platypii/allegiance-and-influence/pull/7) and is separate from these local/live checks.

## Known limits

- Per-character hosted configuration remains an operator JSON file; the solo opponent picker selects only a configured profile. A changed routing configuration needs a new game (or restoration of the original configuration to continue an old one).
- The paired experiment is a controlled two-character conversation using synthetic seats. Ambient AI interactions on the multiplayer board and initial greetings remain deterministic.
- No streaming, cross-round memory, local generative adapter, or tournament/statistical comparison runner yet.
- Input admission uses a conservative byte allowance, not exact tokenization for every remote model. Reported bound overruns reject the decision and block further game calls. Price/usage guards rely on the remote service's reported contract; budgets are per game, not across an account. BYOK is unsupported.
- Exactly-once remote inference/billing is not promised. Unknown or failed attempts retain reservations; remote cancellation may still incur charges.
- Single server process; no public accounts, seat recovery, or distributed scheduling. Old browser tabs must reload after updating the service.

## Next work

The local editable `data/models.json` now uses Haiku by default and for Einstein, Gemini Flash Lite for Churchill, and a selectable Luna profile. Credentials remain in a separate ignored file. A credential-free [verified configuration snapshot](../config/models.verified-2026-10-24.json) records the tested IDs/settings and $1 per-game ceiling. The initial assignment/order controls and a Luna smoke check are complete. The commands are in `docs/model-experiments.md`.

Next, playtest solo pacing and choices, then test longer conversations and concrete character-relevant incentives with repeated comparisons: the short abstract coalition scenario produced no allegiance changes. Then integrate model-driven ambient conversations and move into human playtesting and small gameplay changes. The offline gate remains mandatory throughout.

Client direction: web app now; possible iPhone/Android clients later should reuse the hosted game API. Credentials and model options stay server-side. Mobile packaging remains undecided until gameplay is established.
