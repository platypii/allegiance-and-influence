# Task: OpenRouter character models and paired persuasion experiments

[Task #6](https://github.com/platypii/allegiance-and-influence/issues/6). Parent: modernization epic #1. Builds on merged PR #5 (`03b2a49`). User selected OpenRouter for hosted models and requested different model assignments per character on 2026-10-24.

## Scope

`backend/game/**`, `backend/tests/**`, `frontend/app/**` (mode/status text only; preserve artwork), `frontend/tests/**`, `frontend/playwright.config.ts`, `scripts/**`, `schemas/**`, `tests/fixtures/**`, `experiments/**`, `config/**`, `pyproject.toml`, `uv.lock`, `.env.example`, `README.md`, `docs/**`, `state/PROJECT_STATE.md`, `work/model-conversations.md`.

## Plan and implementation

Use OpenRouter as the hosted boundary. Separate roster personas from model profiles, route by character UID with a default, and pin assignments before the first message. Record requested/returned model and reported upstream provider per attempt. Keep scripted mode as the offline default. The previous direct OpenAI/Ollama plan is superseded for this increment; a local generative adapter remains optional future work.

Add a controlled pair experiment using the same store, runtime, and round rules. Relay each character's reply into the other's conversation, record decisions and usage, share one game budget, and allow swapping models between personas and reversing conversation order. Keep ambient multiplayer-board AI interactions unchanged in this increment.

## Acceptance

- Multiple character models can coexist; model/assignment changes never silently affect saved games.
- Scoped persona prompts and bounded HTTP; structured or explicit prompt-JSON mode with local decision validation.
- Missing usage, malformed/truncated/refused responses, usage overruns, and provider errors cannot mutate arbitrary state or recruit through an invalid decision.
- Model fallbacks are disabled; optional upstream pin and returned identity are recorded. Configured price caps and selected-model reservations apply before calls.
- Both sides of a paired experiment share a budget, pass dialogue to each other, and export actual settings, identity, transcript, decisions, failures, charges, latency, and replay.
- Test evidence clearly distinguishes mocks/scripted output from actual inference. No live calls without a configured key and explicit experiment opt-in.
- Browser labels reflect model mode, saves/replays migrate, original artwork stays intact, and the complete offline gate passes.

## Non-goals

Token streaming, cross-round memory, local model downloads, model rankings, a broad tournament runner, new gameplay mechanics, public hosting, or replacing ambient AI board interactions. Live quality measurement requires model credentials/configuration and a defined spend cap.

## Setup follow-up — 2026-10-24

The user requested file-based model options and identified mobile as a possible later client. Added a setup helper for initialization, public catalog browsing, offline assignment/budget inspection, and hidden terminal key entry. Key files remain separate and ignored; launcher/experiment flags support them. Added credential handling and non-overwrite regression checks. Recorded web-first/mobile-later architecture without adding a mobile framework.
