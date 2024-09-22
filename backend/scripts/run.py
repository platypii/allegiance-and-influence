import os
import sqlite3
from functools import partial
from typing import Annotated

from htw.summarize import summarize_results
from langchain.globals import set_llm_cache
from langchain_anthropic import ChatAnthropic
from langchain_community.cache import SQLiteCache
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from htw.agent.agent import HumanBot, ArgumentaBot, has_agent_been_persuaded
from htw.agent.builder import get_agents
from htw.config import MODEL_NAME
from htw.graph import _build_graph, _run_agent_graph, compile_graphs
from htw.llm import get_antropic_llm


def run_human_vs_bot(llm_builder):
    agents = get_agents(llm_builder, num_agents=1, seed=None)
    human_agent = HumanBot(name="Human", uid="human_player")
    graph_builder = _build_graph(agents[0], human_agent)
    compiled_graphs = compile_graphs([graph_builder], memory=None)
    all_results = _run_agent_graph(compiled_graphs[0], verbose=True)
    all_summarize = summarize_results(all_results, llm_builder)
    print("Human vs Bot Results:")
    print_persuasion_result(all_results)


def run_bot_vs_bot(llm_builder):
    agents = get_agents(llm_builder, num_agents=2, seed=None)
    graph_builder = _build_graph(agents[0], agents[1])
    compiled_graphs = compile_graphs([graph_builder], memory=None)
    all_results = _run_agent_graph(compiled_graphs[0], verbose=True)
    all_summarize = summarize_results(all_results, llm_builder)
    print("Bot vs Bot Results:")
    print_persuasion_result(all_results)


def print_persuasion_result(results):
    for result in results:
        for agent, data in result.items():
            if "messages" in data and data["messages"]:
                last_message = data["messages"][-1].content
                if has_agent_been_persuaded(last_message):
                    print(f"{agent} was persuaded to join the other team!")
                    return
    print("No agent was persuaded. The conversation ended without a clear winner.")


def main():
    set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    llm_builder = partial(get_antropic_llm, model=MODEL_NAME)

    while True:
        mode = input("Enter mode (1 for Human vs Bot, 2 for Bot vs Bot, q to quit): ")
        if mode == "1":
            run_human_vs_bot(llm_builder)
        elif mode == "2":
            run_bot_vs_bot(llm_builder)
        elif mode.lower() == "q":
            break
        else:
            print("Invalid input. Please try again.")


if __name__ == "__main__":
    main()
