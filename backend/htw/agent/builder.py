from htw.agent.agent import ArgumentaBot
from htw.llm import LLMBuilderWithoutModel
import random
import json
import os


def get_agents(llm_builder: LLMBuilderWithoutModel, num_agents: int) -> list[ArgumentaBot]:
    """Generate list of agents."""
    root_message = "You are in a game with one other player. You and this other player are going to have a conversation where we are trying to persuade each other to join each others teams. You will join whatever team but only if it aligns with the characteristics of your character, subjects and themes that you care about. To start, introduce yourself and learn something about the other player. Then try to convince them to join your side but ultimately you want to be on the best side. Your character is influenced by the following attributes: Charisma, Intellect, Stubbornness, Empathy, Influence Range, Loyalty, Curiosity, Consistency. Where you are high on the attribute means you are more likely to be persuaded by that characteristic. You will be given a list of characters and their attributes. You will be randomly assigned one of these characters, never break character. You are particularly susceptible to the core principles behind Dale Carnegie's book 'How to Win Friends and Influence People'."

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
        system_message = f"You are {character['Character']}, {character['Description']}. Your attributes are: Charisma: {character['Charisma']}, Intellect: {character['Intellect']}, Stubbornness: {character['Stubbornness']}, Empathy: {character['Empathy']}, Influence Range: {character['Influence Range']}, Loyalty: {character['Loyalty']}, Curiosity: {character['Curiosity']}, Consistency: {character['Consistency']}. After every message state as ""Status:"" if you want to stay on your current team, say neutral or join the character that you are talking toos team.\n\n{root_message}"
        agents.append(
            ArgumentaBot(
                name=character['Character'],
                uuid=character['UID'],
                system_message=system_message,
                current_status_message="",
                llm_builder=llm_builder,
            )
        )

    return agents
