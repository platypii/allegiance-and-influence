"""Provider-facing shapes. No provider may return arbitrary game mutations."""

from typing import Literal

from pydantic import Field, model_validator

from .models import Character, ChatMessage, Seat, StrictModel


class ProviderIdentity(StrictModel):
    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    prompt_version: str = Field(min_length=1, max_length=80)
    max_input_tokens: int = Field(ge=0)
    max_output_tokens: int = Field(ge=0)
    max_cost_microusd: int = Field(ge=0)


class RuntimePolicy(StrictModel):
    timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    concurrency: int = Field(default=4, ge=1, le=32)
    max_queued: int = Field(default=64, ge=1, le=1000)
    max_attempts: int = Field(default=2, ge=1, le=3)
    call_limit: int = Field(default=200, ge=0)
    token_limit: int = Field(default=200000, ge=0)
    cost_limit_microusd: int = Field(default=0, ge=0)


class AgentRequest(StrictModel):
    schema_version: Literal["1", "2", "3"] = "3"
    purpose: Literal["character_reply", "opponent_argument"] = "character_reply"
    request_id: str
    game_id: str
    round_number: int = Field(ge=1)
    character: Character
    opponent: Seat
    opponent_character: Character | None = None
    opponent_side: Literal[-1, 1]
    messages: list[ChatMessage] = Field(min_length=1, max_length=11)


class Decision(StrictModel):
    dialogue: str = Field(min_length=1, max_length=2000)
    join_opponent: bool

    @model_validator(mode="after")
    def nonblank(self):
        if not self.dialogue.strip():
            raise ValueError("Dialogue cannot be blank")
        return self


class Usage(StrictModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_microusd: int = Field(ge=0)


class Receipt(StrictModel):
    requested_model: str = Field(min_length=1, max_length=120)
    actual_model: str = Field(min_length=1, max_length=120)
    generation_id: str = Field(min_length=1, max_length=200)
    upstream_provider: str | None = Field(default=None, min_length=1, max_length=120)


class ProviderResult(StrictModel):
    schema_version: Literal["1", "2"] = "2"
    decision: Decision
    usage: Usage
    receipt: Receipt | None = None


class AttemptReport(StrictModel):
    request_id: str
    identity: ProviderIdentity | None = None
    receipt: Receipt | None = None
    attempt: int = Field(ge=1)
    status: str
    charged_tokens: int = Field(ge=0)
    charged_cost: int = Field(ge=0)
    usage: Usage | None
    latency_ms: int | None = Field(default=None, ge=0)


class RuntimeReport(StrictModel):
    schema_version: Literal["2"]
    identity: ProviderIdentity | None
    policy: RuntimePolicy | None
    attempts: list[AttemptReport]
