# First live OpenRouter validation — 2026-10-24

Five paired runs completed with 18 successful model replies, plus one successful reply through the real browser UI. All returned model IDs matched their assignments. No output repairs, automatic retries, or application errors occurred in these model calls. This is a compatibility and behavior smoke test, not a model ranking.

## Method

Used the existing coalition scenario with Einstein initially Red and Churchill initially Blue. Haiku/Gemini ran in four conditions: original assignments/order, swapped assignments, reversed speaking order, and both swapped/reversed. Each condition ran once for four replies. A separate two-reply check used Luna as Einstein against Gemini as Churchill. Each opening was fixed scenario text; subsequent messages were model replies. The latest accepted decisions resolved through the game rules.

Configuration snapshot: [`config/models.verified-2026-10-24.json`](../config/models.verified-2026-10-24.json). Model IDs, price ceilings, temperature settings, and token limits were selected from the [OpenRouter catalog](https://openrouter.ai/api/v1/models) on this date. Upstreams were not pinned, so timing reflects the routed service. Prompts and configuration fingerprints are recorded in each local report. No credential or account/key metadata is included in this document.

## Measured results

| Run | Replies | Result | Charged USD | Recruitment decisions |
| --- | ---: | --- | ---: | --- |
| baseline | 4 | completed | $0.000911 | 0 accepted joining |
| luna-smoke | 2 | completed | $0.000416 | 0 accepted joining |
| reversed | 4 | completed | $0.000945 | 0 accepted joining |
| swapped | 4 | completed | $0.000895 | 0 accepted joining |
| swapped-reversed | 4 | completed | $0.000967 | 0 accepted joining |

| Model | Paired-run calls | Median reply latency | Charged USD | Reported upstream |
| --- | ---: | ---: | ---: | --- |
| `google/gemini-3.1-flash-lite` | 9 | 1.167 s | $0.002454 | Google |
| `anthropic/claude-haiku-5.5` | 8 | 2.577 s | $0.001525 | Azure |
| `openai/gpt-6-luna` | 1 | 4.823 s | $0.000155 | OpenAI |

Paired-run charges total **$0.004134**. The browser reply added **$0.000247**, bringing recorded charges to **$0.004381**. Each provider-reported dollar charge is rounded upward to integer micro-USD by the runtime; the account total can therefore be slightly lower. These are inference charges, excluding credit-purchase fees/taxes.

## Observations and limits

All 18 paired replies declined to join the opposing faction. In the baseline transcript, Churchill emphasized defense and practical commitments while Einstein pressed for coherent principles and restraint; the later replies addressed those points. This shows a functioning dialogue exchange, not evidence that persona fidelity or persuasion quality is generally good. Two exchanges per character, one pair, and one run per condition cannot establish model superiority or a stable recruitment rate.

The next gameplay hypothesis is that the present loyalty/commitment prompt and abstract coalition opening encourage refusal. Test longer conversations and explicit, character-relevant incentives as controlled changes; do not change the acceptance rules simply to force a recruitment result. Separate persona, speaking order, sampling, and provider effects in repeated experiments.

## Browser and reproduction evidence

The live browser test created a two-player game, selected distinct characters, sent an argument, and displayed a real Gemini reply with no browser JavaScript errors. The screenshot was inspected and retains the original artwork. The first automation attempt raced the second selection ahead of a WebSocket update; the server returned the expected stale-version conflict and no inference ran. The test now waits until the other browser sees the first target as taken.

Ignored local artifacts:

- `artifacts/live-20261024-*/report.json` and `game.sqlite3`: full settings, transcripts, receipts, accounting, final state, and replay.
- `artifacts/live-browser-accounting.json`: the successful UI request’s accounting.
- `artifacts/screenshots/08-live-model-reply.png`: inspected live UI capture.

Report SHA-256 values (receipts/transcripts remain local):

- `live-20261024-baseline`: `d73eace78bde7b1c79d5e153ca597bf6615466aa6fdca726e5cd83623aaebbda`
- `live-20261024-luna-smoke`: `e32e66df538b9f0a9ef2612c246e125fe5f779863756e4c416f41cc6b5b97554`
- `live-20261024-reversed`: `3e894439e1935ad1c10cf477b4206009173b8a63719b6a59eb86f525a63f55b1`
- `live-20261024-swapped`: `37eea0dcca401ca1457b125dc5796580ca1f87ae15c21b988efde43b2fac765a`
- `live-20261024-swapped-reversed`: `8abfe77da4bac5a7699dc2354952020d667d39774290d1a84b33ede055082e5a`

Repeat the commands in [model-experiments.md](model-experiments.md) with the verified configuration and a separately supplied key. Remote outputs and latency are not deterministic. The offline verifier continues to use mocks/scripted mode and is not evidence of live provider availability.
