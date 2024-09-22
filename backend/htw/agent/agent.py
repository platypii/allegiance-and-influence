from __future__ import annotations

import copy
from enum import Enum
import operator
from typing import Annotated, Callable, Sequence

from anthropic import BaseModel
from htw.config import MODEL_CONFIG
from htw.firebase import listen_to_player_red, update_agent_state
from htw.llm import LLMBuilderWithoutModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict

"""
class BaseMessage(Serializable):

    content: Union[str, list[Union[str, dict]]]

    additional_kwargs: dict = Field(default_factory=dict)

    response_metadata: dict = Field(default_factory=dict)

    type: str
    #The type of the message. Must be a string that is unique to the message type.
    
    #The purpose of this field is to allow for easy identification of the message type
    #when deserializing messages.

    name: Optional[str] = None

    id: Optional[str] = None

    model_config = ConfigDict(
        extra="allow",
    )
"""


class ArgumentSide(Enum):
    ITSELF = "itself"  # 1
    SEMI_ITSELF = "semi-itself"  # 0.5
    NEUTRAL = "neutral"  # 0
    SEMI_OTHER = "semi-other"  # -0.5
    OTHER = "other"  # -1


class ArgumentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str


def serialize_messages(messages: Sequence[BaseMessage]) -> str:
    """Serialize messages for storage in Firebase."""
    messages_str = [f"{m.name}: {m.content}" for m in messages]
    return "\n\n".join(messages_str)


def simplify_messages(messages: Sequence[BaseMessage]) -> list[dict]:
    """Serialize messages for storage in Firebase."""
    return [{"content": m.content, "name": m.name} for m in messages]


def build_input_messages(
    system_message: SystemMessage, messages: Sequence[BaseMessage]
) -> Sequence[BaseMessage]:
    """Build the input messages for the agent."""
    # Swap the roles of the messages so it is always system -> user -> assistant -> user...
    new_messages = []
    for i, message in enumerate(messages[::-1]):
        if i % 2 == 0:
            new_messages.append(HumanMessage(content=message.content))
        elif i % 2 == 1:
            new_messages.append(AIMessage(message.content))
    # Reverse the messages back to the original order.
    new_messages = new_messages[::-1]
    assert new_messages[-1].type == "human"
    # Drop first message if AI type. Anthropic requires first and last message to be human.
    if new_messages[0].type == "ai":
        new_messages = new_messages[1:]
    return [system_message, *new_messages]


def has_agent_been_persuaded(response: str) -> bool:
    """Check if the agent has been persuaded."""
    status_line = response.split("\n")[-1].lower()
    return "status:" in status_line and "join" in status_line


def has_agent_quit(response: str) -> bool:
    """Check if the agent has quit."""
    return "__exit__" in response


class ArgumentaBot:
    def __init__(
        self,
        name: str,
        uuid: str,
        system_message: str,
        current_status_message: str,
        llm_builder: LLMBuilderWithoutModel,
    ):
        self.name = name
        self.uuid = uuid
        self.llm_run_config = RunnableConfig()
        self.llm_config = MODEL_CONFIG
        self.original_system_message = system_message
        self.system_message = SystemMessage(
            (self.original_system_message + "\n\n" + current_status_message).strip()
        )
        self.llm: ChatAnthropic | ChatOpenAI = llm_builder(config=self.llm_config)

        # Game state variables
        self.side = ArgumentSide.NEUTRAL
        self.current_round_id = 0
        self.current_opponent = None
        self.current_chat_messages = []

    def __call__(self, state: ArgumentState) -> ArgumentState:
        """The agent run method that calls llm and adds to the reponse."""
        if isinstance(self.llm, ChatAnthropic):
            input_messages = build_input_messages(
                self.system_message, copy.deepcopy(state["messages"])
            )
        else:
            input_messages = [self.system_message, *state["messages"]]
        self.current_chat_messages = simplify_messages(input_messages)
        response = self.llm.invoke(input_messages)
        response.name = self.name
        # Check if the bot has been persuaded
        persuaded = has_agent_been_persuaded(response.content)
        if persuaded:
            self.update_side(ArgumentSide.OTHER)
        return {"messages": [response]}

    def __str__(self):
        return f"Agent: {self.name} ({self.uuid})"

    def _state_dict(self) -> dict:
        """Generate state dict for FE."""
        return {
            "side": self.side,
            "current_opponent": self.current_opponent,
            "current_chat_messages": self.current_chat_messages,
        }

    def _generate_summary_of_status(self) -> str:
        """Before incrementing the round, generate a summary of the status."""
        if not self.current_chat_messages:
            raise ValueError("No messages to summarize. Call this before incrementing a round.")
        # TODO (Diego): Implement this prompt and make it not suck
        prompt = [
            SystemMessage(
                "Your job is to generate a summary of the messages from this round and come up with a concise understanding of what side this person is on."
            ),
            HumanMessage(serialize_messages(self.current_chat_messages)),
        ]
        response = self.llm.invoke(prompt)
        return response.content

    def increment_round(self):
        """Increment the round and reset the opponent."""
        # First update the agent state
        self.update_db()
        # Then update the status message
        summary = self._generate_summary_of_status()
        self.update_status_message(summary)
        # Then increment the round
        self.current_round_id += 1
        self.current_opponent = None
        self.current_chat_messages = []

    def update_status_message(self, new_status_message: str):
        self.system_message = SystemMessage(
            (self.original_system_message + "\n\n" + new_status_message).strip()
        )

    def update_side(self, new_side: ArgumentSide):
        self.side = new_side

    def update_db(self):
        update_agent_state(
            round_id=self.current_round_id, uuid=self.uuid, agent_dict=self._state_dict()
        )


class HumanBot:
    def __init__(self, name: str, uid: str, listen_func: Callable, update_ai_func: Callable):
        self.name = name
        self.uid = uid
        self.listen_func = listen_func
        self.update_ai_func = update_ai_func

    def __call__(self, state: ArgumentState) -> ArgumentState:
        # Update messages in db
        self.update_ai_func(simplify_messages(state["messages"]))
        print("MESSAGES SO FAR")
        for msg in state["messages"]:
            sender = msg.additional_kwargs.get("sender", "Unknown")
            print(f"{sender}: {msg.content}")
        print("------------------------")
        print("------------------------")
        print("WAITING......")
        result = self.listen_func(self._wait_for_user_input)
        human_msg = HumanMessage(
            result, name=self.name, additional_kwargs={"sender": f"{self.name} ({self.uid})"}
        )
        return {"messages": [human_msg]}

    def __str__(self):
        return f"Agent: {self.name} ({self.uid})"

    def _wait_for_user_input(player_state: dict) -> str:
        """Wait for the user to select an agent."""
        is_user_done = player_state.get("is_done_talking")
        if is_user_done:
            return "__exit__"
        messages = player_state["messages"]
        user_response = messages[-1]["content"]
        return user_response
