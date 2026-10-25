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

## 2026-10-24 — First live candidate configuration and evidence

After the user saved a private key and confirmed its spending cap, selected Haiku, Gemini Flash Lite, and Luna profiles from the public OpenRouter catalog. The local setup assigns Haiku by default/Einstein and Gemini to Churchill, with Luna available as an alternative. A credential-free dated snapshot records exact IDs, parameters, price ceilings, and a $1 per-game ceiling. These are tested starting candidates, not a claim of best models. Keep live experiments separate from the credential-free verifier.

Five paired runs covered assignment swaps, speaking-order reversal, and a third-model smoke check; all 18 replies passed validation. One additional live browser reply succeeded. Total recorded charge was $0.004381. No paired reply accepted recruitment. Preserve that result as evidence and test longer dialogue/concrete incentives next, rather than altering acceptance merely to manufacture successful persuasion. See [live validation](live-validation-2026-10-24.md) for limitations and local report hashes.

## 2026-10-24 — Playtest issues, reliable invites, and solo model opponent

Track actionable playtest bugs/features in repo issues: #8 (session invites) and #9 (single player). The HTTP invite button silently swallowed unavailable clipboard access; construct URLs from game identity and show a selectable fallback plus a lobby link.

Solo creation accepts only a configured opponent profile, reserves Blue, and auto-joins the human as Red. The selected model generates recruitment arguments through the existing durable runtime; target characters keep their independent model assignments and control their own recruitment decisions. Pin the opponent's distinct prompt/model identity and charge all calls to the same game budget. Begin with a documented deterministic target policy, two arguments per round, explicit terminal errors, and human-controlled round advancement. Do not claim model-selected board strategy. Game view v4, agent request v3, and pair report v2 carry the expanded contracts; historical multiplayer state projects without changing its mode or event versions.

## 2026-10-24 — Replit import with optional PostgreSQL persistence

The user selected Replit before DigitalOcean because they already subscribe. Preserve the local SQLite setup and static frontend; add an optional psycopg PostgreSQL store behind the existing transactions. Replit published filesystems are temporary, so publishing must supply DATABASE_URL and cannot silently fall back to SQLite. Explicit local database paths and the offline verifier stay isolated from hosted database credentials. Development and production use separate databases.

One Reserved VM/worker owns the coordinator. A direct/session PostgreSQL connection holds a session advisory lock, and an in-process mutex serializes its short transactions, including budget reservations. Keep model I/O outside transactions. A second coordinator fails startup before recovering jobs; a lost session requires restart rather than automatic reconnect that could relinquish ownership. This is deliberately a small single-server playtest implementation, not a distributed queue. Known Neon transaction-pooler URLs are rejected; other providers must also supply direct/session connections. Overlapping deployment handoff can require stopping the old server first.

Replit Run builds dependencies/assets and starts one Python process on port 3000. Published build and launch are separate. Model configuration is a tracked JSON file and the OpenRouter key stays in Secrets; default import makes no paid calls. Account-side Replit provisioning, module resolution and deployment remain separately verifiable from local/CI evidence. No resources were purchased and no existing SQLite games were migrated.

## 2026-10-25 — Shared game design system and readable mobile play

User feedback in issue #13 called out inconsistent fonts/CSS/text graphics and small mobile text. Introduce shared semantic CSS tokens and a visual reference page. Use a historical strategy treatment: ivory surfaces, dark green ink, brass detail, serif display headings, system sans-serif body/controls, and restrained faction colors. Both font stacks work offline. Compose the existing portraits; replace embedded splash/win lettering with real text. Preserve all 58 original assets and the game contracts.

Replace floating overlays with a board and separate round/session sections. The decorative force simulation allowed character names and targets to collide, so use stable positions while retaining desktop pairing lines. Mobile presents labeled targets in a responsive grid and summaries in the round recap. This changes visual arrangement only; no simulation/game rules depend on those positions.

Use a native conversation dialog to provide keyboard focus containment, Escape, and an inert board while conversing. Full-width on phones, a panel on desktop, with accessible expandable profiles and API errors inside the dialog. Body/form text is at least 16px; secondary labels at least 14px; compact controls at least 44px. Test enlarged text and a complete mobile game rather than only the welcome screen. Real-device keyboards and screen readers remain a hosted playtest check.
