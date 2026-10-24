# Character models and paired persuasion experiments

Hosted inference uses OpenRouter. A character is a persona from `gameplay/characters.json`; a model profile is the implementation playing that persona. Assign several characters the same profile or give each a different one. The game rules and artwork do not depend on model vendor SDKs.

The installed game remains scripted and offline unless `GAME_MODEL_CONFIG` points to a model configuration file. The application does not install models or contact a hosted service at startup. OpenRouter requests begin only when a configured character receives a message. Keys stay in the Python server environment.

## Configure assignments

Copy `config/models.example.json` to an ignored local location such as `data/models.json`. Replace the placeholder IDs with concrete OpenRouter model IDs. The example assigns Einstein to `model_a`, Churchill to `model_b`, and other characters to the scripted control. Set `default_profile` to a hosted profile to make the rest model-driven.

Each profile sets:

- `kind`: `openrouter` or `scripted`; scripted uses `model: "scripted-v1"`.
- `model`: exact OpenRouter ID. Automatic router IDs are rejected. Model-level fallback is disabled; a returned model ID differing from the requested ID fails explicitly and is recorded.
- `upstream_provider`: optional provider slug to restrict routing to one upstream. If omitted, OpenRouter chooses an available endpoint for that model; the reported provider is recorded when supplied, otherwise null. Comparisons without an upstream pin measure the routed service as well as the model.
- `output_format`: `json_schema` by default, with required parameter support and local validation. `prompt_json` omits the API schema for models without structured-output support, still asks for the same JSON shape, and applies identical local validation. There is no silent format fallback or repair call.
- `temperature`: configurable sampling value, or null to omit it for models that do not support sampling controls. Token ceilings and all settings are part of the pinned configuration fingerprint.
- `max_prompt_usd_per_million` and `max_completion_usd_per_million`: price ceilings, not hard-coded current prices. OpenRouter receives these limits with a zero per-request surcharge ceiling. The example uses zero, so paid routes are excluded until explicitly configured.
- `max_input_tokens` and `max_output_tokens`: per-attempt ceilings. The output limit is sent as `max_tokens`. Input admission uses serialized UTF-8 byte size plus an overhead allowance; it is conservative, not an exact native-tokenizer guarantee across every model. Any reported overrun rejects the decision and blocks further calls for that game.

The shared `policy.cost_limit_microusd` is the **whole-game** budget for all character models and retries. One dollar is 1,000,000 micro-USD. Reservations use each selected model's token ceilings and configured price caps, rounded up. A cheap character does not reserve the most expensive character's allowance. Failed or uncertain calls retain conservative reservations; reported charges remain separately visible.

Use a positive game budget and appropriate nonzero price caps for paid models. Budget limits are per game, not per account or across repeated runs. OpenRouter account/key spending controls are the external backstop. This adapter rejects BYOK responses because an OpenRouter-only charge would not cover separate upstream billing. Charges exclude credit-purchase fees and taxes.

```bash
mkdir -p data
cp config/models.example.json data/models.json
# Edit data/models.json: choose models, price ceilings, assignments, and game budget.
# Configure OPENROUTER_API_KEY securely in the server environment; never put it in JSON or Git.
GAME_MODEL_CONFIG=data/models.json bash scripts/run-local.sh
```

`.env.example` lists the variable names; the launcher does not automatically source a dotenv file. Model IDs and assignments are server/operator configuration, not browser-controlled input. Create a new game after changing assignments. New games pin routing and policy at creation. Old games keep their identity and fail explicitly if the running configuration no longer matches; returning to the original configuration restores compatibility. Historical scripted saves remain scripted.

## Paired character experiment

`experiments/pair.json` pairs Einstein (initially Red) and Churchill (initially Blue). A fixed scenario opening is supplied to one character. Its reply becomes the other's next message, alternating for the configured number of exchanges (one to five, two replies per exchange). Both characters independently decide whether to join the other's faction. The latest accepted decisions resolve together at round end, so mutual agreement can exchange allegiances. The first utterance is a scenario seed, not generated evidence.

The runner represents the pair through the game's two player seats, using the same validated commands, durable jobs, per-game ledger, and round resolution as human play. Each model receives its own persona, its opponent's public persona/faction, and its own conversation history. It receives no keys, provider assignments, other games, or unrelated dialogue. Fixed greetings remain presentation text. This controlled experiment does not yet replace ambient AI-pair behavior on the multiplayer board.

```bash
# Offline control; writes to a new directory, never overwrites a prior run.
.venv/bin/python scripts/experiment.py --output artifacts/pair-control

# Explicit live run, using the configured key and bounded game budget.
.venv/bin/python scripts/experiment.py --config data/models.json --live --output artifacts/pair-live-01

# Separate controls for persona/model confounding and order effects.
.venv/bin/python scripts/experiment.py --config data/models.json --live --swap-models --output artifacts/pair-swapped-01
.venv/bin/python scripts/experiment.py --config data/models.json --live --reverse-order --output artifacts/pair-reversed-01
```

A run exports `report.json` and a SQLite database. The report includes evidence type (`scripted`, `mock-http`, or `live-openrouter`), exact configuration, per-character identities, prompt/settings fingerprint, scenario and roster hashes, each reply/decision/failure, per-attempt usage/charge/latency, final factions/scores, and public replay frames. The experiment intentionally exports both participants' transcripts; outputs stay under ignored `artifacts/` and contain no player keys. Ordinary game replay and runtime endpoints remain seat-filtered.

A failed turn stops dialogue generation, records the failure, and resolves only already accepted decisions. The runner exits nonzero and labels the report failed. Failure is not a persuasion loss. No automatic experiment reruns are made. Seeds control game setup; they do not promise deterministic remote inference. Repeat runs, swap model assignments, reverse order, and inspect dialogue before interpreting recruitment rates as model ability. No model ranking or automated personality-quality score is claimed by this increment.

## Contracts, migration, and evidence

Current schemas: game view v3; agent request/result v2 (accepting legacy v1 payloads); runtime report v2; model configuration, pair scenario, and pair report v1. Each has fixtures and executable schema checks. Game view v3 adds model mode and the `persuasion-v1` rule label; old state snapshots project to v3 while retaining their original mode, rule label, and version. SQLite adds route and receipt columns without rewriting old attempts.

The normal verifier clears live configuration/credentials. Adapter tests use HTTP mocks with explicitly labelled receipts; tests exercise mixed-model relay, assignments, shared budgets, conservative failures, timeout/cancellation, malformed and incomplete replies, missing usage, usage overruns, HTTP errors, and privacy. Browser tests include a model-mode fixture server using scripted responses, which verifies interface labels without inference.

Live validation requires a configured OpenRouter key and selected model IDs/spend ceiling. Offline captures prove protocol and lifecycle behavior, not real model availability, personality quality, latency, or persuasion effectiveness.

## Official API basis

Checked 2026-10-24: [chat completion API](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion), [structured output and compatibility](https://openrouter.ai/docs/guides/features/structured-outputs), [provider routing, fallback, and price caps](https://openrouter.ai/docs/guides/routing/provider-selection), and [reported token usage and cost](https://openrouter.ai/docs/cookbook/administration/usage-accounting).
