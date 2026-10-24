from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

Seat = Literal["player_red", "player_blue"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CreateGame(StrictModel):
    num_agents: int = Field(default=6, ge=2, le=23)
    num_rounds: int = Field(default=3, ge=1, le=20)
    seed: int = Field(default=32, ge=0, le=2147483647)


class JoinGame(StrictModel):
    seat: Seat


class CommandBase(StrictModel):
    command_id: str = Field(min_length=16, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    expected_version: int = Field(ge=0)


class Select(CommandBase):
    kind: Literal["select"]
    target: str = Field(min_length=1, max_length=80)


class Message(CommandBase):
    kind: Literal["message"]
    text: str = Field(min_length=1, max_length=2000)


class Done(CommandBase):
    kind: Literal["done"]


class Retry(CommandBase):
    kind: Literal["retry"]


class Cancel(CommandBase):
    kind: Literal["cancel"]


class Advance(CommandBase):
    kind: Literal["advance"]


Command = Annotated[Select | Message | Done | Advance | Retry | Cancel, Field(discriminator="kind")]
COMMAND_ADAPTER = TypeAdapter(Command)


class Character(StrictModel):
    UID: str
    Character: str
    Description: str
    Charisma: int
    Intellect: int
    Stubbornness: int
    Empathy: int
    influence_range: int = Field(alias="Influence Range")
    Loyalty: int
    Curiosity: int
    Consistency: int
    side: Literal[-1, 0, 1]


class ChatMessage(StrictModel):
    name: str
    content: str


class AgentWork(StrictModel):
    request_id: str
    status: Literal["pending", "succeeded", "failed", "cancelled", "interrupted"]
    error: str | None


class Conversation(StrictModel):
    target: str | None
    messages: list[ChatMessage]
    done: bool
    join_opponent: bool
    work: AgentWork | None


class Players(StrictModel):
    player_red: bool
    player_blue: bool


class Conversations(StrictModel):
    player_red: Conversation
    player_blue: Conversation


class Scores(StrictModel):
    player_red: int = Field(ge=0)
    player_blue: int = Field(ge=0)


class Summary(StrictModel):
    pair: list[str] = Field(min_length=2, max_length=2)
    text: str


class RoundHistory(StrictModel):
    round_number: int = Field(ge=1)
    summaries: list[Summary]
    scores: Scores


class GameState(StrictModel):
    schema_version: Literal["3"]
    rules_version: Literal["scripted-v1", "persuasion-v1"]
    id: str
    version: int = Field(ge=0)
    config: CreateGame
    mode: Literal["scripted", "model"]
    phase: Literal["lobby", "selecting", "conversing", "round_complete", "finished"]
    round_number: int = Field(ge=1)
    players: Players
    agents: list[Character]
    conversations: Conversations
    pairings: list[Annotated[list[str], Field(min_length=2, max_length=2)]]
    history: list[RoundHistory]
    scores: Scores
    winner: Seat | Literal["tie"] | None


class GameView(GameState):
    you: Seat | None
