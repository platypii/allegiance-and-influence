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

from htw.agent.agent import HumanBot
from htw.agent.builder import get_agents
from htw.graph import _build_graph, _run_agent_graph, compile_graphs
from htw.llm import get_antropic_llm


def main() -> None:
    # conn = sqlite3.connect("/home/laurel/htw_cache/.checkpoints.sqlite")
    # memory = SqliteSaver(conn)
    # TODO: Add ANTROPHIC_API_KEY to bachrc as environment variable
    set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    llm_model_name = "claude-3-haiku-20240307"
    llm_builder = partial(get_antropic_llm, model=llm_model_name)

    # llm_model_name = "gpt-3.5-turbo"
    # llm_builder = partial(get_openai_llm, model=llm_model_name)

    agent = get_agents(llm_builder)[0]
    human_agent = HumanBot(name="Diego")
    # IMPORTANT: make sure agent is first
    graph_builder = _build_graph(agent, human_agent)
    compiled_graphs = compile_graphs([graph_builder], memory=None)
    all_results = _run_agent_graph(compiled_graphs[0], verbose=False)
    print(all_results)


if __name__ == "__main__":
    main()
