# Project state

Updated 2026-10-21. User authorized autonomous modernization work and explicitly approved merging the reviewed foundation PR.

## Milestones

The self-contained local foundation merged in [PR #3](https://github.com/platypii/allegiance-and-influence/pull/3), commit `d0aff12c4c5447ec9d4a3529a36455b0b88219c5`. [Task #2](https://github.com/platypii/allegiance-and-influence/issues/2) is closed. It establishes the factory, authoritative rules, SQLite persistence, local two-player game, replay, shared roster, and offline verification gate under [epic #1](https://github.com/platypii/allegiance-and-influence/issues/1).

Current increment: provider-neutral agent runtime, branch `codex/agent-runtime`, [task #4](https://github.com/platypii/allegiance-and-influence/issues/4), scope in `work/agent-runtime.md`. This completes the offline runtime portion of milestone 4; live adapters, streaming, and memory remain future increments.

## Implemented in this increment

- Async provider boundary with strict dialogue/recruitment decisions and scoped observations; deterministic scripted adapter preserves the local demo.
- Durable pending jobs and attempt records in SQLite. Result application checks phase, round, character, request identity, and pending status.
- Visible waiting, cancel, and retry controls. Retries preserve the human message; stale or duplicate results cannot append another reply. Replaying an old cancel cannot affect a newer request.
- Bounded concurrency, queue capacity, deadlines, and explicitly classified transient retries. Startup interrupts uncertain work without reissuing it.
- Atomic per-game call/token/cost reservations. Unknown usage retains conservative charges; reported usage is recorded separately. Default allowed spend is zero.
- Pinned provider/model/prompt identity and policy; authenticated, seat-scoped attempt reports. Opponent dialogue and credentials never enter provider observations.
- Game contract v2 and provider/report v1 schemas, documentation, positive/negative fixtures, and executable validation. Stored v1 snapshots/replay remain readable without invented provider events.
- Headless matches use the same runtime and export provider identity/call counts. No cloud service or model API is required.

## Verification evidence

The initial browser run passed both workflows, including pending/cancel/retry, full two-player completion, reload/replay, mobile start, and local-only browser requests. The pending-state screenshot was inspected; the controls fit the existing panel and all original artwork remains in use. The headless runner completed two rounds with eight scripted provider calls and zero model calls. The final shared gate passed after the cancel regression fix: 39 backend tests, two browser workflows, schema/fixture validation, Python lint, frontend build/typechecking, 58 artwork hashes, clean server logs, and patch whitespace.

Artifacts (ignored by Git): `artifacts/screenshots/`, `artifacts/browser-tests/`, `artifacts/e2e-server.log`, `artifacts/headless-replay.json`. Hosted CI results belong to the new PR and are separate from local evidence.

## Known limits

- No generative model adapter, token streaming, cross-round memory, or model benchmark yet. Initial greetings and ambient AI-pair interactions remain deterministic game behavior.
- One server process; no distributed coordination or public account management. Lost tab keys have no seat-recovery flow, and disconnected players can pause progress indefinitely.
- Remote execution/billing cannot be exactly once. Reservations rely on a trustworthy adapter's declared bounds; failed/uncertain attempts retain their charge. Misreported usage blocks further game calls.
- Cancellation prevents late state mutation; adapters must cooperate with cancellation. This is not process isolation for hostile Python code.
- Replay is snapshot playback. Public headless exports omit private conversations.
- All 58 original graphic files are preserved. Foundation changes replaced the remote font with a local fallback and made graph initialization deterministic; exact historical deployment parity is not asserted.
- Tests emit the existing Starlette/httpx migration warning; browser binaries must be installed separately for verification.

## Next increment

Integrate an opt-in generative provider behind the tested contract, starting with scoped recruitment scenarios. Consult current official provider documentation at implementation time; record model/prompt identity, measured latency and usage, and explicit spend configuration. Keep the default demo and verification offline. A local-model adapter is a separate option to evaluate against available hardware.

Then extend the experiment harness with repeated runs, seat swaps, comparable manifests, and failure/cost measurements. Add memory and streaming only with concrete contracts and evidence. Human playtests and incremental gameplay changes follow that measured baseline.
