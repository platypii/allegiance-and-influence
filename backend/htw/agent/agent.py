from __future__ import annotations

import copy
import operator
from typing import Annotated, Callable, Sequence

from htw.config import MODEL_CONFIG
from htw.llm import LLMBuilderWithoutModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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


class ArgumentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str


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


class ArgumentaBot:
    def __init__(self, name: str, system_message: str, llm_builder: LLMBuilderWithoutModel):
        self.name = name
        self.llm_run_config = RunnableConfig()
        self.llm_config = MODEL_CONFIG
        self.system_message = SystemMessage(system_message)
        self.llm: ChatAnthropic | ChatOpenAI = llm_builder(config=self.llm_config)

    def __call__(self, state: ArgumentState) -> ArgumentState:
        """The agent run method that calls llm and adds to the reponse."""
        if isinstance(self.llm, ChatAnthropic):
            input_messages = build_input_messages(
                self.system_message, copy.deepcopy(state["messages"])
            )
        else:
            input_messages = [self.system_message, *state["messages"]]
        # print("STARTING FOR", self.name)
        # for msg in input_messages:
        #     print(msg.type)
        #     print(msg.content)
        #     print("*******")
        response = self.llm.invoke(input_messages)
        return {"messages": [response]}

    def __str__(self):
        return f"Agent: {self.name}"


class HumanBot:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, state: ArgumentState) -> ArgumentState:
        print("MESSAGES SO FAR")
        for msg in state["messages"]:
            print(f"{msg.name}: {msg.content}")
        print("------------------------")
        print("------------------------")
        result = input(">>>")
        if result == "exit":
            raise SystemExit
        return {"messages": [HumanMessage(result)]}

    def __str__(self):
        return f"Agent: {self.name}"
