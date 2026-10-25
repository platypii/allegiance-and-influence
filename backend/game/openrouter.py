"""Bounded OpenRouter HTTP adapter and per-character routing. No SDK auto-retries."""

import json
from decimal import ROUND_CEILING, Decimal, InvalidOperation

import httpx
from pydantic import ValidationError

from .agent_contracts import Decision, ProviderIdentity, ProviderResult, Receipt, Usage
from .model_config import fingerprint
from .persona import DECISION_SCHEMA, PROMPT, messages_for
from .providers import ProviderFailure, RetryableProviderError, ScriptedProvider

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MAX_RESPONSE_BYTES = 262144


class OpenRouterProvider:
    def __init__(self, profile, api_key, transport=None):
        if not api_key or not api_key.strip():
            raise ValueError("Set OPENROUTER_API_KEY in the server environment")
        self.profile = profile.model_copy(deep=True)
        self._api_key, self._transport = api_key, transport
        self.identity = ProviderIdentity(
            provider="openrouter",
            model=profile.model,
            prompt_version="persona-v1:"
            + fingerprint({"prompt": PROMPT, "schema": DECISION_SCHEMA, "profile": profile.model_dump()}),
            max_input_tokens=profile.max_input_tokens,
            max_output_tokens=profile.max_output_tokens,
            max_cost_microusd=profile.cost_ceiling(),
        )

    async def generate(self, request):
        p = self.profile
        messages = messages_for(request)
        # Conservative byte-based admission guard, not a cross-model tokenizer claim.
        input_bound = len(json.dumps([messages, DECISION_SCHEMA], ensure_ascii=False).encode()) + 1024
        if input_bound > p.max_input_tokens:
            raise ProviderFailure("input_limit")
        provider = {
            "allow_fallbacks": False,
            "require_parameters": True,
            "max_price": {
                "prompt": p.max_prompt_usd_per_million,
                "completion": p.max_completion_usd_per_million,
                "request": 0,
            },
        }
        if p.upstream_provider:
            provider["only"] = [p.upstream_provider]
            provider["order"] = [p.upstream_provider]
        body = {
            "model": p.model,
            "messages": messages,
            "stream": False,
            "max_tokens": p.max_output_tokens,
            "temperature": p.temperature,
            "provider": provider,
            "usage": {"include": True},
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "recruitment_decision", "strict": True, "schema": DECISION_SCHEMA},
            },
        }
        if p.temperature is None:
            body.pop("temperature")
        if p.output_format == "prompt_json":
            body.pop("response_format")
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=110, trust_env=False, follow_redirects=False
            ) as client:
                async with client.stream(
                    "POST", ENDPOINT, json=body, headers={"Authorization": "Bearer " + self._api_key}
                ) as response:
                    if response.status_code in {429, 502, 503, 504}:
                        raise RetryableProviderError("OpenRouter temporarily unavailable")
                    if response.status_code != 200:
                        raise ProviderFailure("provider_http_error")
                    chunks, size = [], 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > MAX_RESPONSE_BYTES:
                            raise ProviderFailure("response_too_large")
                        chunks.append(chunk)
            data = json.loads(b"".join(chunks), parse_float=Decimal)
        except httpx.TimeoutException:
            raise ProviderFailure("timeout") from None
        except httpx.RequestError:
            # The outcome may be uncertain; do not automatically retry a transport failure.
            raise ProviderFailure("provider_connection") from None
        except (ValueError, UnicodeError):
            raise ProviderFailure("invalid_response") from None
        return self.parse(data)

    def parse(self, data):
        usage = receipt = None
        try:
            raw = data["usage"]
            cost = raw["cost"]
            if isinstance(cost, bool) or not isinstance(cost, (int, float, Decimal)):
                raise ValueError("Invalid cost")
            cost = Decimal(str(cost))
            if not cost.is_finite() or cost < 0:
                raise ValueError("Invalid cost")
            usage = Usage(
                input_tokens=raw["prompt_tokens"],
                output_tokens=raw["completion_tokens"],
                cost_microusd=int((cost * 1000000).to_integral_value(rounding=ROUND_CEILING)),
            )
            receipt = Receipt(
                requested_model=self.profile.model,
                actual_model=data["model"],
                generation_id=data["id"],
                upstream_provider=data.get("provider"),
            )
            if raw.get("is_byok"):
                raise ProviderFailure("byok_unsupported", usage, receipt)
            if (
                usage.input_tokens > self.identity.max_input_tokens
                or usage.output_tokens > self.identity.max_output_tokens
                or usage.cost_microusd > self.identity.max_cost_microusd
            ):
                raise ProviderFailure("usage_exceeded", usage, receipt)
            if receipt.actual_model != receipt.requested_model:
                raise ProviderFailure("model_mismatch", usage, receipt)
            choices = data["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError("Expected one choice")
            choice = choices[0]
            if choice["message"].get("tool_calls") or data.get("error"):
                raise ValueError("Unexpected tool or error response")
            if choice["finish_reason"] != "stop" or choice["message"].get("refusal"):
                raise ProviderFailure("incomplete_response", usage, receipt)
            decision = Decision.model_validate_json(choice["message"]["content"])
            return ProviderResult(decision=decision, usage=usage, receipt=receipt).model_dump()
        except ProviderFailure:
            raise
        except (KeyError, TypeError, ValueError, InvalidOperation, ValidationError):
            exceeded = usage and (
                usage.input_tokens > self.identity.max_input_tokens
                or usage.output_tokens > self.identity.max_output_tokens
                or usage.cost_microusd > self.identity.max_cost_microusd
            )
            raise ProviderFailure(
                "usage_exceeded" if exceeded else "invalid_response", usage, receipt
            ) from None


class CharacterRouter:
    def __init__(self, config, api_key=None, transport=None):
        self.config = config.model_copy(deep=True)
        self.profiles = {
            name: ScriptedProvider() if p.kind == "scripted" else OpenRouterProvider(p, api_key, transport)
            for name, p in self.config.profiles.items()
        }
        identities = [p.identity for p in self.profiles.values()]
        self.identity = ProviderIdentity(
            provider="character-router",
            model="assignments:" + fingerprint(config.model_dump()),
            prompt_version="routing-v1:" + fingerprint([i.model_dump() for i in identities]),
            max_input_tokens=max(i.max_input_tokens for i in identities),
            max_output_tokens=max(i.max_output_tokens for i in identities),
            max_cost_microusd=max(i.max_cost_microusd for i in identities),
        )
        self.routes = {
            "*": self.for_character("*").identity.model_dump(),
            **{uid: self.for_character(uid).identity.model_dump() for uid in config.characters},
        }

    def for_character(self, uid):
        return self.profiles[self.config.characters.get(uid, self.config.default_profile)]

    async def generate(self, request):
        return await self.for_character(request.character.UID).generate(request)
