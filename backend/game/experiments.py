"""Paired character conversations using the same command, job, budget, and rule paths."""

import secrets
import uuid
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .agent_contracts import Decision, ProviderIdentity, RuntimePolicy, RuntimeReport
from .core import SEATS, view
from .model_config import ModelConfig, fingerprint
from .models import ChatMessage, CreateGame, GameView, StrictModel
from .runtime import AgentRuntime
from .store import Store


class PairScenario(StrictModel):
    schema_version: Literal["1"] = "1"
    name: str = Field(min_length=1, max_length=100)
    characters: list[str] = Field(min_length=2, max_length=2)
    opening: str = Field(min_length=1, max_length=2000)
    exchanges: int = Field(default=2, ge=1, le=5)
    seed: int = Field(default=32, ge=0, le=2147483647)
    first_seat: Literal["player_red", "player_blue"] = "player_red"

    @model_validator(mode="after")
    def distinct(self):
        if len(set(self.characters)) != 2 or not self.opening.strip():
            raise ValueError("Use two distinct characters and a nonblank opening")
        return self


class ExperimentTurn(StrictModel):
    character: str
    request_id: str
    status: str
    error: str | None
    decision: Decision | None
    messages: list[ChatMessage]


class PairReport(StrictModel):
    schema_version: Literal["2"] = "2"
    evidence: Literal["scripted", "mock-http", "live-openrouter"]
    status: Literal["completed", "failed"]
    scenario: PairScenario
    scenario_hash: str
    roster_hash: str
    provider: ProviderIdentity
    configuration: ModelConfig | None
    assignments: dict[str, ProviderIdentity]
    policy: RuntimePolicy
    turns: list[ExperimentTurn]
    accounting: dict[str, RuntimeReport]
    final: GameView
    replay: list[GameView]


async def run_pair(path: Path, roster, scenario, provider, policy, *, evidence):
    """One game budget for both models. First utterance is a fixed scenario seed, not inference."""
    if not set(scenario.characters) <= {c["UID"] for c in roster}:
        raise ValueError("Scenario contains an unknown character UID")
    store = Store(path, roster, provider.identity, policy, routes=getattr(provider, "routes", None))
    game = store.create(
        CreateGame(num_agents=2, num_rounds=1, seed=scenario.seed).model_dump(), pair=scenario.characters
    )
    runtime = AgentRuntime(store, provider, policy)
    tokens = {seat: secrets.token_hex(24) for seat in SEATS}
    turns = []

    async def command(seat, kind, **fields):
        state = store.load(game["id"])
        state, actor = store.apply(
            game["id"],
            tokens[seat],
            {"kind": kind, "command_id": uuid.uuid4().hex, "expected_version": state["version"], **fields},
        )
        if kind == "message":
            runtime.schedule(state, actor)
            await runtime.drain()
        return store.load(game["id"])

    try:
        for seat, token in tokens.items():
            store.join(game["id"], seat, token)
        # Each synthetic seat represents the faction of the opposite character.
        await command("player_red", "select", target=scenario.characters[1])
        await command("player_blue", "select", target=scenario.characters[0])
        seat, text = scenario.first_seat, scenario.opening
        status = "completed"
        for _ in range(scenario.exchanges * 2):
            state = await command(seat, "message", text=text)
            chat = state["conversations"][seat]
            work = chat["work"]
            ok = work["status"] == "succeeded"
            turns.append(
                ExperimentTurn(
                    character=chat["target"],
                    request_id=work["request_id"],
                    status=work["status"],
                    error=work["error"],
                    messages=chat["messages"],
                    decision=Decision(
                        dialogue=chat["messages"][-1]["content"], join_opponent=chat["join_opponent"]
                    )
                    if ok
                    else None,
                )
            )
            if not ok:
                status = "failed"
                break
            text = chat["messages"][-1]["content"]
            seat = SEATS[1] if seat == SEATS[0] else SEATS[0]
        # Failures remain failures; the game still resolves accepted decisions and can be replayed.
        for seat in SEATS:
            await command(seat, "done")
        final = store.load(game["id"])
        assignments = {
            uid: (
                provider.for_character(uid).identity
                if hasattr(provider, "for_character")
                else provider.identity
            )
            for uid in scenario.characters
        }
        return PairReport(
            evidence=evidence,
            status=status,
            scenario=scenario,
            scenario_hash=fingerprint(scenario.model_dump()),
            roster_hash=fingerprint(roster),
            provider=provider.identity,
            configuration=getattr(provider, "config", None),
            assignments=assignments,
            policy=policy,
            turns=turns,
            accounting={seat: store.runtime_report(game["id"], seat) for seat in SEATS},
            final=view(final, None),
            replay=store.replay(game["id"], None),
        )
    finally:
        await runtime.close()
