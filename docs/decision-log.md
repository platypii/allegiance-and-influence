# Architecture decisions

## 2026-10-21 — Local application first

User direction: remove external dependencies where practical, preserve graphics, keep multiplayer possible, and autonomously execute the modernization plan.

Implementation: one Python/FastAPI process serves a static Next.js export, HTTP commands, WebSocket snapshots, and embedded SQLite storage. Loopback is the default; LAN exposure is explicit. Firebase and remote fonts are absent from the new runtime. Node is a build tool, not a runtime server requirement.

Reason: the original browser uses no necessary server-rendered features, and local ownership of rules is needed for both multiplayer and agent experiments. Static export was built and browser-tested. Alternative deferred: Firebase emulator, because it adds a service while retaining the old coupling.

## 2026-10-21 — Honest scripted baseline

The first model-free implementation has deliberately simple, documented rules. It is labeled "Scripted demo" in the UI, saved states, and CLI output. It verifies infrastructure and preservation of the visual identity. It does not claim old LLM behavior or new gameplay quality.

Use explicit phases, validated commands, per-game versions, hashed seat keys, and transactional snapshots/events. Replay displays committed views. Character JSON is shared by both runtimes. Keep legacy source available for characterization without installing its dependency stack.

## 2026-10-21 — Build and verification dependencies

Use Python 3.12 with a root uv lockfile and current pinned Next.js/React packages with an npm lockfile. The root environment excludes legacy LangChain/LangGraph/Firebase. Add Playwright and pytest as development tools. A static build/typecheck, contract checks, meaningful API tests, browser flows, and asset preservation form the shared gate. Live models and their budgets remain a later task.

## 2026-10-21 — Operating boundaries

This baseline has one authoritative server process. It supports local/LAN multiplayer, not public account management or distributed deployment. Do not add speculative managed-service adapters. Add capacity/hosting infrastructure when a measured workload and deployment decision require it.

## 2026-10-21 — Provider boundary and durable work

PR #3 was merged after the user's review. Task #4 extracts human-facing character replies into an asynchronous provider protocol. SQLite commits pending requests before execution and binds accepted results to request/round/character identity. Replies and recruitment decisions are validated; the core retains scoring authority. The default scripted provider preserves the demo. Ambient AI pair resolution is still deterministic.

Provider identity and policy are pinned per game; attempts reserve calls/tokens/micro-USD before invocation. Uncertain failures retain their reservation, and reported usage is distinct from budget charge. Cost defaults to zero. Restart interrupts work rather than automatically reissuing potentially billed calls. Cancelled/late work cannot mutate a later conversation.

Game view v2 projects v1 saved states and replay frames without rewriting their recorded history. New clients expose pending/cancel/retry controls; original artwork remains unchanged. Live inference, token streaming, cross-round memory, and paid evaluation are subsequent scoped tasks.

## 2026-10-24 — Hosted models through OpenRouter, assigned per character

The user selected OpenRouter as the hosted gateway so experiments can vary models per character. Personas remain roster data; named model profiles define inference settings and character UID overrides choose the profile. New games pin the configuration, and each job reserves the selected model's allowance. Requested/returned model IDs and upstream receipts remain distinct. Model fallback is disabled; upstream routing can be pinned. Structured-output compatibility is explicit, with a prompt-JSON option that retains local validation.

Paired persuasion experiments reuse the two-seat game, durable runtime, and shared ledger. Each synthetic seat represents the other character's faction; the characters' replies alternate until the fixed turn bound or a failure, then accepted decisions resolve together. Exported transcripts are explicitly experimental evidence, separate from the seat-filtered multiplayer API. Live inference remains opt-in; no credential was available during implementation. Direct OpenAI and Ollama adapters are deferred in favor of the user's hosted gateway choice.

## 2026-10-24 — Operator setup file and future mobile clients

Keep named model profiles, character overrides, and experiment budgets in `data/models.json`. Keep credentials in a separate owner-only file or server environment; an explicitly selected key file takes precedence. A setup helper creates files without overwriting, lists the public model catalog, and checks local assignments without inference. No key is collected in conversation or embedded in game reports.

The user wants a web app now and may later ship iPhone/Android clients. Preserve the server-owned HTTP/WebSocket boundary and keep model credentials/budgets there. Defer the mobile wrapper/native choice until gameplay is established, with hosted identity/recovery and reconnect behavior as prerequisites.
