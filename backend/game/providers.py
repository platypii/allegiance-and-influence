"""Providers are asynchronous and cancellation-cooperative; no network dependency here."""

import asyncio
from typing import Protocol

from .agent_contracts import AgentRequest, ProviderIdentity


class RetryableProviderError(Exception):
    """An explicit transient failure. Retries consume another reserved attempt."""


class AgentProvider(Protocol):
    identity: ProviderIdentity

    async def generate(self, request: AgentRequest) -> dict: ...


class ScriptedProvider:
    identity = ProviderIdentity(
        provider="scripted",
        model="scripted-v1",
        prompt_version="scripted-v1",
        max_input_tokens=0,
        max_output_tokens=0,
        max_cost_microusd=0,
    )

    def __init__(self, delay_seconds=0.0):
        if not 0 <= delay_seconds <= 5:
            raise ValueError("Scripted delay must be between 0 and 5 seconds")
        self.delay_seconds = delay_seconds

    async def generate(self, request: AgentRequest) -> dict:
        await asyncio.sleep(self.delay_seconds)
        count = sum(message.name == request.opponent for message in request.messages)
        dialogue = (
            "Tell me more about how we would work together."
            if count < 2
            else "You have made your case. I will join your faction when this round ends."
        )
        return {
            "schema_version": "1",
            "decision": {"dialogue": dialogue, "join_opponent": count >= 2},
            "usage": {"input_tokens": 0, "output_tokens": 0, "cost_microusd": 0},
        }
