import os
import sqlite3
from functools import partial
from typing import Annotated

from langchain.globals import set_llm_cache
from langchain_anthropic import ChatAnthropic
from langchain_community.cache import SQLiteCache
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from htw.agent.agent import HumanBot, ArgumentaBot
from htw.agent.builder import get_agents
from htw.graph import _build_graph, _run_agent_graph, compile_graphs
from htw.llm import get_antropic_llm

def run_human_vs_bot(llm_builder):
    agents = get_agents(llm_builder, num_agents=1)
    human_agent = HumanBot(name="Human")
    graph_builder = _build_graph(agents[0], human_agent)
    compiled_graphs = compile_graphs([graph_builder], memory=None)
    all_results = _run_agent_graph(compiled_graphs[0], verbose=True)
    print("Human vs Bot Results:")
    print(all_results)

def run_bot_vs_bot(llm_builder):
    agents = get_agents(llm_builder, num_agents=2)
    graph_builder = _build_graph(agents[0], agents[1])
    compiled_graphs = compile_graphs([graph_builder], memory=None)
    all_results = _run_agent_graph(compiled_graphs[0], verbose=True)
    print("Bot vs Bot Results:")
    print(all_results)

def main():
    set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    llm_model_name = "claude-3-haiku-20240307"
    llm_builder = partial(get_antropic_llm, model=llm_model_name)

    while True:
        mode = input("Enter mode (1 for Human vs Bot, 2 for Bot vs Bot, q to quit): ")
        if mode == '1':
            run_human_vs_bot(llm_builder)
        elif mode == '2':
            run_bot_vs_bot(llm_builder)
        elif mode.lower() == 'q':
            break
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()
