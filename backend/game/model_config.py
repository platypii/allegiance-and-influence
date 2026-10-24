"""Explicit, credential-free model assignments; server configuration, never browser input."""

import hashlib
import json
import os
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .agent_contracts import RuntimePolicy
from .models import StrictModel


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ModelProfile(StrictModel):
    kind: Literal["scripted", "openrouter"] = "openrouter"
    model: str = Field(min_length=1, max_length=120)
    max_input_tokens: int = Field(default=32768, ge=1024, le=131072)
    max_output_tokens: int = Field(default=512, ge=64, le=4096)
    max_prompt_usd_per_million: float = Field(default=0.0, ge=0, le=1000, allow_inf_nan=False)
    max_completion_usd_per_million: float = Field(default=0.0, ge=0, le=1000, allow_inf_nan=False)
    upstream_provider: str | None = Field(default=None, min_length=1, max_length=120)
    output_format: Literal["json_schema", "prompt_json"] = "json_schema"
    temperature: float | None = Field(default=0.7, ge=0, le=2, allow_inf_nan=False)

    @model_validator(mode="after")
    def explicit_model(self):
        if self.kind == "scripted" and self.model != "scripted-v1":
            raise ValueError("Scripted profiles must use scripted-v1")
        if self.kind == "openrouter" and ("/" not in self.model or self.model.startswith("openrouter/")):
            raise ValueError("Choose a concrete OpenRouter model ID, not an automatic router")
        return self

    def cost_ceiling(self):
        # USD per million tokens is numerically micro-USD per token. Round upward.
        return int(
            (
                Decimal(str(self.max_prompt_usd_per_million)) * self.max_input_tokens
                + Decimal(str(self.max_completion_usd_per_million)) * self.max_output_tokens
            ).to_integral_value(rounding=ROUND_CEILING)
        )


class ModelConfig(StrictModel):
    schema_version: Literal["1"] = "1"
    default_profile: str
    profiles: dict[str, ModelProfile] = Field(min_length=1, max_length=24)
    characters: dict[str, str] = Field(default_factory=dict, max_length=23)
    policy: RuntimePolicy = Field(default_factory=RuntimePolicy)

    @model_validator(mode="after")
    def assignments_exist(self):
        for profile in [self.default_profile, *self.characters.values()]:
            if profile not in self.profiles:
                raise ValueError("Assignment refers to an unknown profile")
        return self

    def validate_roster(self, roster):
        if set(self.characters) - {c["UID"] for c in roster}:
            raise ValueError("Model configuration contains an unknown character UID")


def configured_provider(roster):
    from .openrouter import CharacterRouter
    from .providers import ScriptedProvider

    path = os.environ.get("GAME_MODEL_CONFIG")
    if not path:
        return ScriptedProvider(float(os.environ.get("GAME_SCRIPTED_DELAY_MS", "0")) / 1000), RuntimePolicy()
    config = ModelConfig.model_validate_json(Path(path).read_text())
    config.validate_roster(roster)
    return CharacterRouter(config, os.environ.get("OPENROUTER_API_KEY")), config.policy
