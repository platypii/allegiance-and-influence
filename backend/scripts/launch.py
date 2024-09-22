import time
from functools import partial

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

from htw.agent.agent import ArgumentaBot, HumanBot
from htw.agent.builder import get_agents
from htw.config import MODEL_NAME
from htw.firebase import (
    connect,
    delete_current_state,
    get_player_blue,
    get_player_red,
    get_round_state,
    listen_to_player_blue,
    listen_to_player_red,
    listen_to_round_state,
    update_current_pairing,
    update_current_round_state,
)
from htw.graph import (
    _build_graph,
    build_graphs,
    compile_graphs,
    run_graphs_parallel,
)
from htw.llm import LLMBuilderWithoutModel, get_antropic_llm


def both_users_ready(
    app_state,
    round_id: int,
    agents: list[ArgumentaBot],
    human_red: HumanBot,
    human_blue: HumanBot,
    llm_builder: LLMBuilderWithoutModel,
) -> str:
    """Return the agent selected by the user."""
    if app_state.event_type == "put":
        # You can technically get the fine grained put updates of each subkey in app_state.path
        # and app_state.app_data but it's easier to get the entire state and check if the keys
        app_data = get_round_state()
        if (
            app_data
            and app_data.get("player_red", {}).get("choose")
            and app_data.get("player_blue", {}).get("choose")
        ):
            red_agent = [ag for ag in agents if ag.uuid == app_data["player_red"]["choose"]][0]
            blue_agent = [ag for ag in agents if ag.uuid == app_data["player_blue"]["choose"]][0]

            # Remaining agents
            remaining_agents = [
                ag
                for ag in agents
                if ag.uuid
                not in [app_data["player_red"]["choose"], app_data["player_blue"]["choose"]]
            ]
            # First get the graph for agent vs agent
            graphs = build_graphs(remaining_agents, seed=round_id)
            # Now add the human to agent graph. Make sure to add the agent first
            graphs.append(_build_graph(red_agent, human_red))
            graphs.append(_build_graph(blue_agent, human_blue))
            # Add the pairing to the state
            pairs = []
            for g in graphs:
                pair = []
                for agent_name in g.nodes.keys():
                    for ag in agents:
                        if ag.name == agent_name:
                            pair.append(ag.uuid)
                if len(pair) == 1:
                    if pair[0] == red_agent.uuid:
                        pair.append("player_red")
                    else:
                        pair.append("player_blue")
                pairs.append(tuple(pair))
            update_current_pairing(round_id, pairs)

            compiled_graphs = compile_graphs(graphs, memory=None)
            all_results = run_graphs_parallel(compiled_graphs, llm_builder)
            update_current_round_state(
                round_id=None,
                current_agents=None,
                player_red_messages=None,
                player_blue_messages=None,
                agents_complete=True,
            )
            for ag in agents:
                ag.increment_round()


def run_round(
    round_id: int,
    agents: list[ArgumentaBot],
    human_red: HumanBot,
    human_blue: HumanBot,
    llm_builder: LLMBuilderWithoutModel,
):
    delete_current_state()
    both_users_ready_partial = partial(
        both_users_ready,
        round_id=round_id,
        agents=agents,
        human_red=human_red,
        human_blue=human_blue,
        llm_builder=llm_builder,
    )
    # Update the list of current agents
    update_current_round_state(
        round_id=round_id,
        current_agents=[ag.uuid for ag in agents],
        player_red_messages=None,
        player_blue_messages=None,
        agents_complete=False,
    )
    listen_to_round_state(both_users_ready_partial)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the persuasion game with a specified number of agents."
    )
    parser.add_argument(
        "--num-agents",
        type=int,
        default=2,
        help="Number of agents to use in the game (default: 2)",
    )
    parser.add_argument(
        "--num-rounds",
        type=int,
        default=10,
        help="Number of rounds to run the game for (default: 10)",
    )
    args = parser.parse_args()

    num_agents = args.num_agents
    num_rounds = args.num_rounds

    connect()

    set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    llm_builder = partial(get_antropic_llm, model=MODEL_NAME)
    agents = get_agents(llm_builder, num_agents=num_agents, seed=32)

    human_agent_red = HumanBot(
        name="Human Red",
        uuid="player_red",
        listen_func=listen_to_player_red,
        get_func=get_player_red,
        update_ai_func=lambda messages: update_current_round_state(
            round_id=None,
            current_agents=None,
            player_red_messages=messages,
            player_blue_messages=None,
            agents_complete=False,
        ),
    )
    human_agent_blue = HumanBot(
        name="Human Blue",
        uuid="player_blue",
        listen_func=listen_to_player_blue,
        get_func=get_player_blue,
        update_ai_func=lambda messages: update_current_round_state(
            round_id=None,
            current_agents=None,
            player_red_messages=None,
            player_blue_messages=messages,
            agents_complete=False,
        ),
    )
    for round_id in range(num_rounds):
        run_round(round_id, agents, human_agent_red, human_agent_blue, llm_builder)
        while True:
            # Wait under agents are completed
            round_state = get_round_state()
            if round_state.get("agents_complete"):
                break
            else:
                time.sleep(5)


if __name__ == "__main__":
    main()
