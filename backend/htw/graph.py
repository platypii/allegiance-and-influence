import concurrent.futures
from functools import partial
import random

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from htw.agent.agent import ArgumentaBot, ArgumentState, has_agent_been_persuaded
from htw.config import LANGGRAPH_CONFIG, SEED_MESSAGE, MODEL_NAME, LLM_CONFIG
from htw.llm import get_antropic_llm

from typing import List

def random_pairings(
    agents: list[ArgumentaBot], seed: int
) -> list[tuple[ArgumentaBot, ArgumentaBot]]:
    """Implement a random pairing of agents algorithm."""
    if len(agents) % 2 != 0:
        raise ValueError("Number of agents must be even.")
    random.seed(seed)
    shuffled_agents = agents.copy()
    random.shuffle(shuffled_agents)
    return [(agents[i], agents[i + 1]) for i in range(0, len(shuffled_agents), 2)]


def _build_graph(agent1: ArgumentaBot, agent2: ArgumentaBot) -> StateGraph:
    graph_builder = StateGraph(ArgumentState)
    graph_builder.add_node(agent1.name, agent1)
    graph_builder.add_node(agent2.name, agent2)

    graph_builder.add_conditional_edges(agent1.name, lambda state: "end" if has_agent_been_persuaded(state["messages"][-1].content) else "continue", {"continue": agent2.name, "end": END})
    graph_builder.add_conditional_edges(agent2.name, lambda state: "end" if has_agent_been_persuaded(state["messages"][-1].content) else "continue", {"continue": agent1.name, "end": END})
    graph_builder.add_edge(START, agent1.name)
    return graph_builder


def build_graphs(agents: list[ArgumentaBot], seed: int) -> list[StateGraph]:
    used_names: set[str] = set()
    for agent in agents:
        if agent.name in used_names:
            raise ValueError(f"Agent name {agent.name} is not unique.")

    pairs = random_pairings(agents, seed=seed)
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


def summarize_conversation(messages: List[BaseMessage], llm_builder) -> str:
    """
    Summarize the entire conversation between two agents.
    
    Args:
    messages (List[BaseMessage]): List of messages from the conversation.
    llm_builder: Function to build the LLM.

    Returns:
    str: A concise summary of the conversation.
    """
    llm = llm_builder(model=MODEL_NAME, config=LLM_CONFIG)
    
    # Flatten the list of messages
    flattened_messages = [msg for sublist in messages for msg in (sublist if isinstance(sublist, list) else [sublist])]
    
    conversation_text = "\n".join([f"{msg.additional_kwargs.get('sender', 'Unknown')}: {msg.content}" for msg in flattened_messages])
    
    prompt = [
        SystemMessage(content="You are a highly efficient summarizer."),
        HumanMessage(content=f"Based on the following conversation, summarize what happened and call out any decisive moments where one argument won over the other. The summary should be no more than 5 simple bullets. Be extremely concise and to the point.\n\nConversation:\n{conversation_text}")
    ]
    
    response = llm.invoke(prompt)
    return response.content


def _run_agent_graph(compiled_graph: CompiledStateGraph, verbose: bool, llm_builder) -> list[dict]:
    initial_state = ArgumentState(
        messages=[BaseMessage(content=SEED_MESSAGE, type="human", additional_kwargs={'sender': 'SYSTEM'})],
        sender="STARTING"
    )
    results = []
    all_messages = []
    try:
        for event in compiled_graph.stream(initial_state, config=LANGGRAPH_CONFIG, debug=False):
            if verbose:
                for k, v in event.items():
                    sender = v['messages'][0].additional_kwargs.get('sender', k)
                    print(f"{sender}: {v['messages'][0].content}")
                    print()
            results.append(event)
            all_messages.extend(event[k]['messages'] for k in event)
            
            # Check if any agent has been persuaded
            if any(v.get('stop_reason') == 'persuaded' for v in event.values()):
                if verbose:
                    print("Conversation ended: An agent has been persuaded!")
                break
    except Exception as e:
        print(e)
    
    # Generate and print the summary
    summary = summarize_conversation(all_messages, llm_builder)
    print("\nConversation Summary:")
    print(summary)
    
    return results


def run_graphs(compiled_graphs: list[CompiledStateGraph], verbose: bool, llm_builder) -> list[list[dict]]:
    """In same thread, run the compiled graphs serially."""
    results = []
    for i, graph in enumerate(compiled_graphs):
        if verbose:
            if i != 0:
                print("\n\n")
            print("------------------")
            print("NEW GRAPH")
            print("------------------")
        results.append(_run_agent_graph(graph, verbose, llm_builder))
    return results


def run_graphs_parallel(compiled_graphs: list[CompiledStateGraph]) -> list[list[dict]]:
    """In separate threads, run the compiled graphs."""
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        _run_agent_graph_partial = partial(_run_agent_graph, verbose=False)
        # Submit each graph to the executor
        future_to_graph = {
            executor.submit(_run_agent_graph_partial, graph): graph for graph in compiled_graphs
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_graph):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"An error occurred while running a graph: {e}")

    return results
