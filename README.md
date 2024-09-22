# How to Win Friends and Influence Agents

## Overview

"How to Win Friends and Influence Agents" is a strategic multiplayer game inspired by Dale Carnegie's seminal work, "How to Win Friends and Influence People". In this unique turn-based experience, players compete to build the largest faction by persuading AI-controlled historical figures to join their cause.

## Key Features

- **Dynamic Character Interactions**: Engage with AI agents representing diverse historical figures, each with unique traits and motivations.
- **Influence Mechanics**: Implement key principles from Carnegie's work to sway opinions and build alliances.
- **Multi-layered Strategy**: Combine direct persuasion with indirect influence as AI agents interact autonomously.
- **Hexagonal Game Board**: Navigate a virtual "room" where nodes represent individual AI agents and connections show ongoing interactions.

## Game Setup

- **Players**: 2 human players (Player A and Player B)
- **AI Agents**: Multiple unaligned historical figures
- **Game Board**: Hexagonal layout with nodes for each agent

## Gameplay

1. **Turn-Based System**: Players take turns having one-on-one conversations with AI agents.
2. **Conversation Interface**: Text-based dialogue with a 5-message limit per interaction.
3. **Agent-Agent Interactions**: AI figures converse autonomously between player turns, influencing opinions and allegiances.
4. **Scoring**: Points awarded for each AI agent in a player's faction.
5. **Victory Condition**: The player with the largest faction at the end of the game wins.

## Project Structure

```
/src
  /ai
    - agent.py
    - conversation.py
  /game
    - board.py
    - player.py
    - turn.py
  /ui
    - interface.py
    - render.py
/tests
  - test_agent.py
  - test_game.py
/docs
  - game_design.md
  - api_reference.md
```

## Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/your-username/how-to-win-friends-and-influence-agents.git
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the game:
   ```
   python src/main.py
   ```

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) file for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

- Inspired by Dale Carnegie's "How to Win Friends and Influence People"
- Special thanks to our AI and game design teams