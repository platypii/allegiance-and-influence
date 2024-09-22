import os
from typing import Callable
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

LLMBuilderWithoutModel = Callable[[str, dict], ChatAnthropic]


def get_antropic_llm(config: dict, model: str) -> ChatAnthropic:
    return ChatAnthropic(
        model=model,
        **config,
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )


def get_openai_llm(config: dict, model: str) -> ChatAnthropic:
    return ChatOpenAI(
        model=model,
        **config,
        api_key=os.environ["OPENAI_API_KEY"],
    )
