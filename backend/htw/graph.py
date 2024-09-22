import concurrent.futures
import random
from functools import partial

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from htw.agent.agent import ArgumentaBot, ArgumentState, has_agent_quit
from htw.config import LANGGRAPH_CONFIG, SEED_MESSAGE


def random_pairings(agents: list[ArgumentaBot]) -> list[tuple[ArgumentaBot, ArgumentaBot]]:
    """Implement a random pairing of agents algorithm."""
    if len(agents) % 2 != 0:
        raise ValueError("Number of agents must be even.")
    shuffled_agents = agents.copy()
    random.shuffle(shuffled_agents)
    return [(agents[i], agents[i + 1]) for i in range(0, len(shuffled_agents), 2)]


def _graph_exit(state: ArgumentState) -> str:
    if state["persuaded"]:
        print("HERE", state.get("name"), state.get("sender"), "WAS PERSUADED WTIH")
        return END
    elif has_agent_quit(state["messages"][-1].content):
        return END
    return "continue"


def _build_graph(agent1: ArgumentaBot, agent2: ArgumentaBot) -> StateGraph:
    graph_builder = StateGraph(ArgumentState)
    graph_builder.add_node(agent1.name, agent1)
    graph_builder.add_node(agent2.name, agent2)

    graph_builder.add_conditional_edges(
        agent1.name, _graph_exit, {"continue": agent2.name, END: END}
    )
    graph_builder.add_conditional_edges(
        agent2.name, _graph_exit, {"continue": agent1.name, END: END}
    )
    graph_builder.add_edge(START, agent1.name)
    return graph_builder


def build_graphs(agents: list[ArgumentaBot]) -> list[StateGraph]:
    used_names: set[str] = set()
    for agent in agents:
        if agent.name in used_names:
            raise ValueError(f"Agent name {agent.name} is not unique.")

    pairs = random_pairings(agents)
    graphs = []
    for agent1, agent2 in pairs:
        graph = _build_graph(agent1, agent2)
        graphs.append(graph)
    return graphs


def compile_graphs(graphs: list[StateGraph], memory: SqliteSaver) -> list[CompiledStateGraph]:
    compiled_graphs = []
    for graph in graphs:
        compiled_graph = graph.compile(checkpointer=memory)
        compiled_graphs.append(compiled_graph)
    return compiled_graphs


def _run_agent_graph(compiled_graph: CompiledStateGraph, i: int, verbose: bool) -> list[dict]:
    initial_state = ArgumentState(
        messages=[
            BaseMessage(content=SEED_MESSAGE, type="human", additional_kwargs={"sender": "SYSTEM"})
        ],
        sender="STARTING",
    )
    results = []
    try:
        for event in compiled_graph.stream(initial_state, config=LANGGRAPH_CONFIG, debug=False):
            if verbose:
                for k, v in event.items():
                    sender = v["messages"][0].additional_kwargs.get("sender", k)
                    print(f"{sender}: {v['messages'][0].content}")
                    print()
            results.append(event)
    except Exception as e:
        print("ERROR")
        print(e)
    return i, results


def run_graphs(compiled_graphs: list[CompiledStateGraph], verbose: bool) -> list[list[dict]]:
    """In same thread, run the compiled graphs serially."""
    results = []
    for i, graph in enumerate(compiled_graphs):
        if verbose:
            if i != 0:
                print("\n\n")
            print("------------------")
            print("NEW GRAPH")
            print("------------------")
        results.append(_run_agent_graph(graph, i, verbose)[1])
    return results


def run_graphs_parallel(
    compiled_graphs: list[CompiledStateGraph], timeout: float = None
) -> list[list[dict]]:
    results = [None] * len(compiled_graphs)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_graph = {
            executor.submit(partial(_run_agent_graph, i=i, verbose=False), graph): graph
            for i, graph in enumerate(compiled_graphs)
        }

        try:
            for future in concurrent.futures.as_completed(future_to_graph, timeout=timeout):
                try:
                    result_tuple = future.result()
                    idx, result = result_tuple
                    results[idx] = result
                except Exception as e:
                    print(f"An error occurred while running a graph: {e}")
        except concurrent.futures.TimeoutError:
            print("Execution timed out")
    print("LAUREL FIND ME...I AM DONE WITH PARALLEL")
    return results
