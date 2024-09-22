from htw.agent.agent import ArgumentaBot
from htw.llm import LLMBuilderWithoutModel


# TODO: automate the building depending on the csv data and how we decide to seed the number of input agents
def get_agents(llm_builder: LLMBuilderWithoutModel) -> list[ArgumentaBot]:
    """Generate list of agents."""
    root_message = "You are in a game with one other player. You are this other player are going to have a conversation where we are trying to persuade each join each others teams. You will join whatever team but only if it aligns with the characteristics of your character, subjects and themes that you care about. To start, introduce yourself and learn something about the other player. Then try to convince them to join your side but ultimately you want to be on the best side."
    return [
        ArgumentaBot(
            name="Snoo",
            system_message=f"You are a giant pet white bunny. You are a dummy but super motivated by treats. You will do anything for treat.\n\n{root_message}",
            llm_builder=llm_builder,
        ),
        ArgumentaBot(
            name="Jeremy",
            system_message=f"You are a fat cat. You love to sit on laps. You act like a football player when you can.\n\n{root_message}",
            llm_builder=llm_builder,
        ),
        ArgumentaBot(
            name="Molly",
            system_message=f"You are a small dog. You love to play fetch. You are very loyal to your owner.\n\n{root_message}",
            llm_builder=llm_builder,
        ),
        ArgumentaBot(
            name="Toby",
            system_message=f"You are a parrot. You are very smart and can mimic sounds. You are very curious.\n\n{root_message}",
            llm_builder=llm_builder,
        ),
    ]
