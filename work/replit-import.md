# Scope: direct GitHub import into Replit

Issue [#11](https://github.com/platypii/allegiance-and-influence/issues/11), under epic #1. The user selected Replit because they already subscribe. No cloud resources or paid inference are provisioned by this change.

## Plan

Keep the static Next.js frontend, Python coordinator, artwork, and local SQLite launch. Add an optional PostgreSQL store for durable hosted games, a single-process ownership lock, Replit build/preview/publish commands, and an import/Secrets/runbook. Use the existing game and job transactions; do not fork game rules or add Firebase. Default import remains scripted until model configuration is explicitly enabled.

## Acceptance

- GitHub import has explicit Python/Node dependencies, one HTTP/WebSocket port, and Run/build/publish commands.
- Published startup requires PostgreSQL; local SQLite stays service-free.
- PostgreSQL preserves games, seats, replay, jobs, and budget accounting across restart; rollback/concurrency and single-coordinator ownership are tested against a real server.
- The offline gate remains credential-free. CI separately exercises PostgreSQL with disposable data.
- Document database/Secrets setup, smallest suitable Reserved VM, model profiles, backup, restart behavior, and verification limits. No artwork changes.

## Assess / Resolve

Implemented `.replit`, pinned build/preview/production scripts, optional psycopg storage, transaction/ownership boundaries, and the import/Secrets/operations guide. Existing SQLite data and artwork remain intact; production has no filesystem fallback. PostgreSQL uses one direct/session connection and fails closed on lost ownership; overlapping deployments may require an explicit stop/start.

Verification: the full offline gate passed with 92 backend tests and 5 browser workflows, schema/fixture checks, lint, static build/typechecking, all 58 artwork hashes, and clean server logs. PostgreSQL checks are deliberately skipped by that gate and run separately. The real PostgreSQL 18.6 suite passed all 19 cases; together with the two hosted-entrypoint checks the targeted command passed 21 tests. Evidence includes transactional rollback, concurrent seat and budget writes, single-owner rejection/release, initialization failure cleanup, lost-session failure, durable restart/replay/charges, solo and mixed-model play, HTTP/WebSocket contracts, and the actual production shell launcher serving assets and preserving a game across process restart. No paid model calls were made.

A fresh source-only copy (no installed dependencies, saved games, or credentials) successfully ran the Replit build script using Python 3.12 and Node 22. Replit TOML and shell syntax checks passed. The documented pg_dump/pg_restore commands were also exercised against separate disposable databases and preserved the complete game. Ignored logs: `artifacts/replit-build.log`, `artifacts/replit-offline-verify.log`, `artifacts/replit-postgres-verify.log` (18-case run before adding the explicit pooler rejection test; the final 21-test targeted run passed in the terminal).

Replit account-side import/publishing remains a separate check: local/CI tests cannot prove platform module resolution, database proxy compatibility, or publishing succeeds. No Replit resource was provisioned. The current default branch remains unchanged until the PR is merged; the prepared branch can be selected after GitHub import.
