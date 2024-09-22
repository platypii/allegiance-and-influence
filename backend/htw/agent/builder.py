from htw.agent.agent import ArgumentaBot
from htw.config import ROOT_MESSAGE_NO_TEAM
from htw.llm import LLMBuilderWithoutModel
import random
import json
import os


def get_agents(
    llm_builder: LLMBuilderWithoutModel, num_agents: int, seed: int
) -> list[ArgumentaBot]:
    """Generate list of agents."""
    random.seed(seed)

    # Load characters from JSON file
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_path = os.path.join(current_dir, "..", "gameplay", "characters.json")
    with open(json_path, "r") as f:
        characters = json.load(f)

    # Set the maximum number of agents to the total number of characters
    max_agents = len(characters)

    # Limit the number of agents to the maximum available or the requested number, whichever is smaller
    num_agents = min(num_agents, max_agents)

    # Randomly select characters
    selected_characters = random.sample(characters, num_agents)

    # Create ArgumentaBot instances
    agents = []
    for character in selected_characters:
        character_message = f"You are {character['Character']}, {character['Description']}. Your attributes are: Charisma: {character['Charisma']}, Intellect: {character['Intellect']}, Stubbornness: {character['Stubbornness']}, Empathy: {character['Empathy']}, Influence Range: {character['Influence Range']}, Loyalty: {character['Loyalty']}, Curiosity: {character['Curiosity']}, Consistency: {character['Consistency']}."
        system_message = f"{ROOT_MESSAGE_NO_TEAM}"
        agents.append(
            ArgumentaBot(
                name=character["Character"],
                uuid=character["UID"],
                system_message=system_message,
                character_message=character_message,
                current_status_message="",
                llm_builder=llm_builder,
                update_ai_func=None,
                llm_callback=None,
            )
        )

    return agents
