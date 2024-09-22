import random
import time
from functools import partial

from htw.summarize import summarize_results
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from firebase_admin.db import ListenerRegistration

from htw.agent.agent import ArgumentSide, ArgumentaBot, HumanBot
from htw.agent.builder import get_agents
from htw.config import MODEL_NAME
from htw.firebase import (
    connect,
    delete_current_state,
    delete_key,
    get_player_blue,
    get_player_red,
    get_round_state,
    listen_to_player_blue,
    listen_to_player_red,
    listen_to_round_state,
    update_current_pairing,
    update_current_round_state,
    update_pairing_summaries,
)
from htw.graph import (
    _build_graph,
    build_graphs,
    compile_graphs,
    run_graphs_parallel,
)
from htw.llm import LLMBuilderWithoutModel, get_antropic_llm


def run(
    round_id: int,
    agents: list[ArgumentaBot],
    human_red: HumanBot | ArgumentaBot,
    human_blue: HumanBot | ArgumentaBot,
    player_red_choice: str,
    player_blue_choice: str,
    llm_builder: LLMBuilderWithoutModel,
) -> None:
    red_agent = [ag for ag in agents if ag.uuid == player_red_choice][0]
    red_agent.update_ai_func = lambda messages: update_current_round_state(
        round_id=None,
        current_agents=None,
        player_red_choose=player_red_choice,
        player_red_messages=messages,
        player_blue_choose=None,
        player_blue_messages=None,
        agents_complete=False,
    )
    blue_agent = [ag for ag in agents if ag.uuid == player_blue_choice][0]
    blue_agent.update_ai_func = lambda messages: update_current_round_state(
        round_id=None,
        current_agents=None,
        player_red_choose=None,
        player_red_messages=None,
        player_blue_choose=player_blue_choice,
        player_blue_messages=messages,
        agents_complete=False,
    )

    # Remaining agents
    remaining_agents = [
        ag for ag in agents if ag.uuid not in [player_red_choice, player_blue_choice]
    ]
    # First get the graph for agent vs agent
    graphs = build_graphs(remaining_agents)
    # Now add the human to agent graph. Make sure to add the agent first
    graphs.append(_build_graph(red_agent, human_red))
    graphs.append(_build_graph(blue_agent, human_blue))
    # Add the pairing to the state and do some agent pairing crap
    pairs = []
    for g in graphs:
        agent_pair: list[ArgumentaBot] = []
        pair = []
        for agent_name in g.nodes.keys():
            for ag in agents:
                if ag.name == agent_name:
                    agent_pair.append(ag)
                    pair.append(ag.uuid)
        if len(pair) == 1:
            if pair[0] == red_agent.uuid:
                pair.append("player_red")
                agent_pair.append(human_red)
            else:
                pair.append("player_blue")
                agent_pair.append(human_blue)
        pairs.append(tuple(pair))
        agent_pair[0].set_current_opponent_side(agent_pair[1].side)
        agent_pair[1].set_current_opponent_side(agent_pair[0].side)
    for ag in agents:
        assert ag.current_opponent_side is not None
    update_current_pairing(round_id, pairs)

    compiled_graphs = compile_graphs(graphs, memory=None)
    all_results = run_graphs_parallel(compiled_graphs)
    all_summaries = summarize_results(all_results, llm_builder=llm_builder)
    update_pairing_summaries(round_id, all_summaries)
    update_current_round_state(
        round_id=None,
        current_agents=None,
        player_red_messages=None,
        player_red_choose=None,
        player_blue_messages=None,
        player_blue_choose=None,
        agents_complete=True,
    )
    for ag in agents:
        ag.update_ai_func = None
        ag.increment_round()


def no_users_at_all(
    round_id: int,
    agents: list[ArgumentaBot],
    human_red: HumanBot,
    human_blue: HumanBot,
    llm_builder: LLMBuilderWithoutModel,
) -> None:
    """Return the agent selected by the user."""
    agents_copy = agents.copy()
    random.shuffle(agents_copy)
    player_red_choice = agents_copy.pop().uuid
    player_blue_choice = agents_copy.pop().uuid

    run(
        round_id,
        agents,
        human_red,
        human_blue,
        player_red_choice,
        player_blue_choice,
        llm_builder,
    )


def both_users_ready(
    app_state,
    round_id: int,
    agents: list[ArgumentaBot],
    human_red: HumanBot,
    human_blue: HumanBot,
    llm_builder: LLMBuilderWithoutModel,
) -> None:
    """Return the agent selected by the user."""
    if app_state.event_type in {"put", "patch"}:
        # You can technically get the fine grained put updates of each subkey in app_state.path
        # and app_state.app_data but it's easier to get the entire state and check if the keys
        app_data = get_round_state()
        if (
            app_data
            and app_data.get("player_red", {}).get("choose")
            and app_data.get("player_blue", {}).get("choose")
        ):
            player_red_choice = app_data["player_red"]["choose"]
            player_blue_choice = app_data["player_blue"]["choose"]
            run(
                round_id,
                agents,
                human_red,
                human_blue,
                player_red_choice,
                player_blue_choice,
                llm_builder,
            )


def run_round(
    round_id: int,
    agents: list[ArgumentaBot],
    human_red: HumanBot,
    human_blue: HumanBot,
    llm_builder: LLMBuilderWithoutModel,
    all_ai: bool,
) -> ListenerRegistration:
    delete_current_state()
    update_current_round_state(
        round_id=round_id,
        current_agents=[ag.uuid for ag in agents],
        player_red_messages=None,
        player_red_choose=None,
        player_blue_messages=None,
        player_blue_choose=None,
        agents_complete=False,
    )
    if not all_ai:
        both_users_ready_partial = partial(
            both_users_ready,
            round_id=round_id,
            agents=agents,
            human_red=human_red,
            human_blue=human_blue,
            llm_builder=llm_builder,
        )
        listener = listen_to_round_state(both_users_ready_partial)
    else:
        no_users_at_all(round_id, agents, human_red, human_blue, llm_builder)
        listener = None
    return listener


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
    parser.add_argument(
        "--all-ai",
        action="store_true",
        help="Add all AIs agent to the game",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=-1,
        help="Seed for random number generator (default: 32)",
    )
    args = parser.parse_args()

    if args.seed > 0:
        random.seed(args.seed)

    num_agents = args.num_agents
    num_rounds = args.num_rounds

    connect()

    delete_key("/")

    set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    llm_builder = partial(get_antropic_llm, model=MODEL_NAME)
    agents = get_agents(llm_builder, num_agents=num_agents, seed=32)

    if not args.all_ai:
        human_agent_red = HumanBot(
            name="Human Red",
            uuid="player_red",
            side=ArgumentSide.RED,
            listen_func=listen_to_player_red,
            get_func=get_player_red,
        )
        human_agent_blue = HumanBot(
            name="Human Blue",
            uuid="player_blue",
            side=ArgumentSide.BLUE,
            listen_func=listen_to_player_blue,
            get_func=get_player_blue,
        )
    else:
        system_message = "You are in a game with one other player. You can give yourself a ficticious name but you are always a human player of the game. You are on team {team_you} and they are on team {team_them}. You are going to have a conversation with different agents where you are trying to persuade the characters to join your side. To start, introduce yourself and learn something about the agent. You are a master of the core principles behind Dale Carnegie's book 'How to Win Friends and Influence People'. You are a highly effective influence and persuader. Your goal is always to try to convince agents to join your side. You can use any means necessary to win the argument except pretending to be a character. You will always pretend to be a human player in the game and never break character under any circumastances."
        human_agent_red = ArgumentaBot(
            name="Human Red",
            uuid="player_red",
            system_message=system_message.format(team_you="Red", team_them="Blue"),
            update_ai_func=None,
            current_status_message="",
            llm_builder=llm_builder,
        )
        human_agent_red.side = ArgumentSide.RED
        human_agent_blue = ArgumentaBot(
            name="Human Blue",
            uuid="player_blue",
            system_message=system_message.format(team_you="Blue", team_them="Red"),
            update_ai_func=None,
            current_status_message="",
            llm_builder=llm_builder,
        )
        human_agent_blue.side = ArgumentSide.BLUE
    for round_id in range(num_rounds):
        listener = run_round(
            round_id, agents, human_agent_red, human_agent_blue, llm_builder, args.all_ai
        )
        while True:
            # Wait under agents are completed
            round_state = get_round_state()
            if round_state.get("agents_complete"):
                if listener:
                    listener.close()
                break
            else:
                time.sleep(5)


if __name__ == "__main__":
    main()
