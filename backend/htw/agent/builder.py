from htw.agent.agent import ArgumentaBot
from htw.llm import LLMBuilderWithoutModel
import random
import json
import os

# TODO: automate the building depending on the csv data and how we decide to seed the number of input agents
def get_agents(llm_builder: LLMBuilderWithoutModel, num_agents: int) -> list[ArgumentaBot]:
    """Generate list of agents."""
    root_message = "You are in a game with one other player. You are this other player are going to have a conversation where we are trying to persuade each join each others teams. You will join whatever team but only if it aligns with the characteristics of your character, subjects and themes that you care about. To start, introduce yourself and learn something about the other player. Then try to convince them to join your side but ultimately you want to be on the best side. Your character is influenced by the following attributes: Charisma, Intellect, Stubbornness, Empathy, Influence Range, Loyalty, Curiosity, Consistency. Where you are high on the attribute means you are more likely to be persuaded by that characteristic."
    
    # Load characters from JSON file
    # Go up one directory level from the current file's location
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_path = os.path.join(current_dir, '..', 'gameplay', 'characters.json')
    with open(json_path, 'r') as f:
        characters = json.load(f)
    
    # Randomly select characters
    selected_characters = random.sample(characters, min(num_agents, len(characters)))
    
    # Create ArgumentaBot instances
    agents = []
    for character in selected_characters:
        system_message = f"You are {character['Character']}, {character['Description']}. Your attributes are: Charisma: {character['Charisma']}, Intellect: {character['Intellect']}, Stubbornness: {character['Stubbornness']}, Empathy: {character['Empathy']}, Influence Range: {character['Influence Range']}, Loyalty: {character['Loyalty']}, Curiosity: {character['Curiosity']}, Consistency: {character['Consistency']}.\n\n{root_message}"
        agents.append(
            ArgumentaBot(
                name=character['Character'],
                system_message=system_message,
                llm_builder=llm_builder,
            )
        )
    
    # If we need more agents than available characters, create generic ones
    for i in range(len(agents), num_agents):
        generic_system_message = f"You are a unique individual with your own personality. Create your own character and backstory.\n\n{root_message}"
        agents.append(
            ArgumentaBot(
                name=f"Agent{i+1}",
                system_message=generic_system_message,
                llm_builder=llm_builder,
            )
        )
    
    return agents
