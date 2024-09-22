from __future__ import annotations

import copy
from enum import Enum
import operator
import re
import time
from typing import Annotated, Callable, Sequence

from anthropic import BaseModel
from htw.config import MODEL_CONFIG
from htw.firebase import get_round_state, listen_to_player_red, update_agent_state
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
    BLUE = 1
    SEMI_BLUE = 0.5
    NEUTRAL = 0
    SEMI_RED = -0.5
    RED = -1


class ArgumentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    persuaded: bool


def _remove_status_line(response: str) -> str:
    return response.rsplit("Status:", 1)[0].strip()


def simplify_messages(messages: Sequence[BaseMessage]) -> list[dict]:
    """Serialize messages for storage in Firebase."""
    return [{"content": _remove_status_line(m.content), "name": m.name} for m in messages]


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


def has_agent_been_persuaded(response: str, llm: ChatAnthropic | ChatOpenAI) -> bool:
    """Check if the agent has been persuaded."""
    prompt = [
        SystemMessage(
            "You are a discriminative classifier who determines if someone is persuaded to join the other person's team or not.\n\nLook at the last status sentence from a conversation and determine if the person has been persuaded to join the other person's team. Output `Score: #` where `#` is -1 if they have strongly not been persuaded, 0 if they are neutral, and 1 if they have strongly been persuaded."
        ),
        HumanMessage(content=response),
    ]
    response = llm.invoke(prompt)
    score = int(re.search(r"Score: (-?\d)", response.content).group(1))
    return score > 0


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
        update_ai_func: Callable,
    ):
        self.name = name
        self.uuid = uuid
        self.llm_run_config = RunnableConfig()
        self.llm_config = MODEL_CONFIG
        self.original_system_message = system_message
        self.current_status_message = current_status_message
        self.system_message = SystemMessage(
            (self.original_system_message + "\n\n" + self.current_status_message).strip()
        )
        self.llm: ChatAnthropic | ChatOpenAI = llm_builder(config=self.llm_config)
        self.update_ai_func = update_ai_func

        # Game state variables
        self.side = ArgumentSide.NEUTRAL
        self.current_round_id = 0
        self.current_opponent_side: ArgumentSide = None
        self.current_chat_messages = []

    def __call__(self, state: ArgumentState) -> ArgumentState:
        """The agent run method that calls llm and adds to the reponse."""
        if isinstance(self.llm, ChatAnthropic):
            input_messages = build_input_messages(
                self.system_message, copy.deepcopy(state["messages"])
            )
        else:
            input_messages = [self.system_message, *state["messages"]]
        response = self.llm.invoke(input_messages)
        # Always skip the first "hello, tell me about yourself" SEED message
        self.current_chat_messages = simplify_messages(state["messages"][1:]) + [
            {"content": _remove_status_line(response.content), "name": self.uuid}
        ]
        for msg in self.current_chat_messages:
            print(msg["content"][-500:])
        print("GOT RESPONSE FROM", self.name, "simplified to", len(self.current_chat_messages))
        if self.update_ai_func:
            self.update_ai_func(self.current_chat_messages)
        # Check if the bot has been persuaded
        persuaded = has_agent_been_persuaded(response.content, self.llm)
        if persuaded:
            if self.current_opponent_side is None:
                raise ValueError("Agent has been persuaded but the opponent side is not set.")
            self.update_side(self.current_opponent_side)
        ai_message = AIMessage(
            response.content,
            name=self.uuid,
            additional_kwargs={"sender": f"{self.name} ({self.uuid})"},
        )
        return {"messages": [ai_message], "persuaded": persuaded}

    def __str__(self):
        return f"Agent: {self.name} ({self.uuid})"

    def _state_dict(self) -> dict:
        """Generate state dict for FE."""
        return {
            "side": self.side.value,
            "current_chat_messages": self.current_chat_messages,
        }

    def _generate_summary_of_status(self) -> str:
        """Before incrementing the round, generate a summary of the status."""

        def _serialize_messages(messages: Sequence[BaseMessage]) -> str:
            """Serialize messages for storage in Firebase."""
            messages_str = [f"{m['name']}: {m['content']}" for m in messages]
            return "\n\n".join(messages_str)

        if not self.current_chat_messages:
            raise ValueError("No messages to summarize. Call this before incrementing a round.")
        prompt = [
            SystemMessage(
                "Your job is to generate a summary of the messages from this round and come up with a concise understanding of what side this person is on."
            ),
            HumanMessage(_serialize_messages(self.current_chat_messages)),
        ]
        response = self.llm.invoke(prompt)
        return response.content

    def set_current_opponent_side(self, opponent_side: ArgumentSide):
        self.current_opponent_side = opponent_side

    def increment_round(self):
        """Increment the round and reset the opponent."""
        # First update the agent state
        self.update_db()
        # Then update the status message
        summary = self._generate_summary_of_status()
        self.current_status_message += (
            f"\n\nConversation Summary of Conversation {self.current_round_id+1}:\n{summary}"
        ).strip()
        self.update_system_message_with_new_status()
        # Then increment the round
        self.current_round_id += 1
        self.current_chat_messages = []
        self.current_opponent_side = None

    def update_system_message_with_new_status(self):
        self.system_message = SystemMessage(
            (self.original_system_message + "\n\n" + self.current_status_message).strip()
        )

    def update_side(self, new_side: ArgumentSide):
        self.side = new_side

    def update_db(self):
        update_agent_state(
            round_id=self.current_round_id, uuid=self.uuid, agent_dict=self._state_dict()
        )


class HumanBot:
    def __init__(
        self,
        name: str,
        uuid: str,
        side: ArgumentSide,
        listen_func: Callable,
        get_func: Callable,
    ):
        self.name = name
        self.uuid = uuid
        self.side = side
        self.listen_func = listen_func
        self.get_func = get_func
        self.user_input_from_last_message = None

    def __call__(self, state: ArgumentState) -> ArgumentState:
        # for msg in state["messages"][:-1]:
        #     sender = msg.additional_kwargs.get("sender", "Unknown")
        #     print(f"{sender}: {msg.content}")
        # print("------------------------")
        # print("------------------------")
        print(f"WAITING......{self.name}")
        listener = self.listen_func(self._wait_for_user_input)
        while True:
            print(".", self.user_input_from_last_message, end="", flush=True)
            if self.user_input_from_last_message is not None:
                listener.close()
                break
            else:
                time.sleep(0.5)
        print(f"DONE WAITING... {self.name}")
        human_msg = HumanMessage(
            self.user_input_from_last_message,
            name=self.uuid,
            additional_kwargs={"sender": f"{self.name} ({self.uuid})"},
        )
        self.user_input_from_last_message = None
        return {"messages": [human_msg], "persuaded": False}

    def __str__(self):
        return f"Agent: {self.name} ({self.uuid})"

    def _wait_for_user_input(self, app_state) -> None:
        """Wait for the user to select an agent."""
        print("IN WAIT FOR USER INPUT", self.name, app_state.event_type, app_state.path)
        if app_state.event_type in {"put", "patch"}:
            # You can technically get the fine grained put updates of each subkey in app_state.path
            # and app_state.app_data but it's easier to get the entire state and check if the keys
            app_data = self.get_func()
            if app_data and app_data.get("messages"):
                is_user_done = app_data.get("done_talking")
                if is_user_done:
                    self.user_input_from_last_message = "__exit__"
                    print(f"Exiting forcefuly from {self.name}")
                    return
                messages = app_data["messages"]
                if messages[-1]["name"] == self.uuid:
                    print(f"Got message from {self.name}: {messages[-1]['content']}")
                    self.user_input_from_last_message = messages[-1]["content"]
        print("NOTHING TO DO", self.name)
        return

    def set_current_opponent_side(self, opponent_side: ArgumentSide):
        pass
