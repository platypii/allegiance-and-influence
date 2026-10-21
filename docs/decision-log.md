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
