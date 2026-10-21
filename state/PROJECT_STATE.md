# Project state

Updated 2026-10-21. User authorized autonomous work on the modernization plan.

## Active milestone

Self-contained local foundation and software-factory bootstrap, branch `codex/local-game-foundation`. Task: `work/local-foundation.md`, [GitHub #2](https://github.com/platypii/allegiance-and-influence/issues/2), under [epic #1](https://github.com/platypii/allegiance-and-influence/issues/1).

## Implemented

- New `backend/game/` runtime: pure scripted transitions, server-owned game sessions, validated commands, SQLite snapshots and command journal, HTTP API, WebSocket updates.
- Configurable complete two-player matches, isolated seats, target collision handling, five-message limit, explicit round progression, final scores and ties.
- Tab-scoped player keys stored as hashes on the server; private dialogue projection; duplicate-command protection and stale-version rejection.
- Restart recovery of committed state; browser replay; a headless scripted runner using the same core/store.
- Static Next.js export served by Python. Removed Firebase, D3, and remote Google font dependencies from the current frontend. The legacy Python experiment is retained but excluded from the new root environment.
- Canonical shared roster; all 58 original graphic files preserved byte-for-byte. Added labels, keyboard-operable portrait buttons, reduced-motion handling, and narrow-screen adjustments.
- Root uv environment and lockfile, npm lockfile, local launcher, setup script, protocol schemas/fixtures, offline verification gate, GitHub CI and task/PR templates, architecture/runbook documentation.

## Verification evidence

The backend suite passed 18 tests. The first browser pass completed both workflows but exposed a server-side WebSocket close exception; that exception was fixed and the verifier now checks server logs. The final gate passed: 18 backend tests, 2 browser workflows, schema/failing-fixture validation, Python lint, static build/typechecking, 58 asset hashes, and a clean browser server log. The headless runner also completed a two-round match with zero model calls.

Artifacts (ignored by Git): `artifacts/screenshots/`, `artifacts/browser-tests/`, `artifacts/e2e-server.log`, `artifacts/headless-replay.json`. Screenshots of the board, chat, result, and mobile view were inspected. These establish the local baseline; the historical Firebase deployment was not run, so exact historical visual/behavioral parity is not asserted.

## Known limits

- Scripted replies and recruitment rules are explicit demo behavior. No live model adapter, streaming inference, long-term agent memory, or model benchmark is implemented yet.
- One server process; no distributed coordination or public account management. Lost tab keys have no seat-recovery flow, and disconnected players can pause progress indefinitely.
- Replay is recorded snapshot playback, not reconstruction from events alone. Public headless exports omit private conversations.
- Original artwork is intact. The remote handwriting font was replaced by the existing local cursive fallback; the graph retains its force rules but now starts from deterministic positions and respects reduced motion.
- Test dependencies emit a Starlette notice about future httpx migration; tests currently pass. Browser binaries must be installed separately for verification.

## Next task

Extract the scripted policy behind a provider-neutral agent runtime. Define validated decision output, pending-work lifecycle, cancellation, retry/idempotence, latency/token/cost accounting, and fake-provider conformance tests before integrating a live provider. Select current models through measured scenarios with a stated spend cap. Preserve the working local baseline as the regression gate.

Later: richer memory, repeated controlled experiments, disconnected-seat recovery, then human playtests and gameplay changes.

## Closeout — first local foundation

The complete offline verification gate passed on 2026-10-21. Browser requests were confined to the local server. Captures were visually reviewed, including the corrected narrow-screen score/round layout. Runtime behavior is ready for local review; live models and gameplay design remain subsequent work.

The documented setup command also passed with the committed lockfiles. GitHub task records are created; hosted CI evidence belongs to the draft PR and is not implied by the local verification result.
