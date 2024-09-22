from htw.config import LLM_CONFIG
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from htw.llm import LLMBuilderWithoutModel
from langchain_openai import ChatOpenAI


def summarize_conversation(messages: list[BaseMessage], llm_builder: LLMBuilderWithoutModel) -> str:
    """
    Summarize the entire conversation between two agents.

    Args:
    messages (List[BaseMessage]): List of messages from the conversation.
    llm_builder: Function to build the LLM.

    Returns:
    str: A concise summary of the conversation.
    """
    llm: ChatAnthropic | ChatOpenAI = llm_builder(config=LLM_CONFIG)

    # Flatten the list of messages
    flattened_messages = [
        msg for sublist in messages for msg in (sublist if isinstance(sublist, list) else [sublist])
    ]

    conversation_text = "\n".join(
        [
            f"{msg.additional_kwargs.get('sender', 'Unknown')}: {msg.content}"
            for msg in flattened_messages
        ]
    )

    prompt = [
        SystemMessage(content="You are a highly efficient summarizer."),
        HumanMessage(
            content=f"Based on the following conversation, summarize what happened and call out any decisive moments where one argument won over the other. The summary should be no more than 5 simple bullets (use * for bullets). Be extremely concise and to the point.\n\nConversation:\n{conversation_text}\n\nStart the summary with 'Here's a concise 5 bullet summary:'"
        ),
    ]

    response = llm.invoke(prompt)
    result = response.content.replace("Here's a concise 5 bullet summary:", "").strip()
    return result


def summarize_results(
    all_results: list[list[dict]], llm_builder: LLMBuilderWithoutModel
) -> list[str]:
    all_summaries = []
    for results in all_results:
        all_messages = []
        for dct in results:
            all_messages.extend([d["messages"] for d in dct.values()])
        all_summaries.append(summarize_conversation(all_messages, llm_builder))
    return all_summaries
