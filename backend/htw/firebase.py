import os
from typing import Any, Callable

import firebase_admin
from firebase_admin import credentials, db


def connect() -> bool:
    if not os.path.exists("/home/laurel/aistrinkers_firebase_admin.json"):
        return False
    cred = credentials.Certificate("/home/laurel/aistrinkers_firebase_admin.json")
    firebase_admin.initialize_app(
        cred, {"databaseURL": "https://aistinkers-default-rtdb.firebaseio.com"}
    )
    return True


def update_key(key: str, value: Any) -> bool:
    try:
        ref = db.reference(key)
        ref.set(value)
        return True
    except Exception as e:
        print(f"Error updating key: {e}")
        return False


def delete_key(key: str) -> bool:
    try:
        ref = db.reference(key)
        ref.delete()
        return True
    except Exception as e:
        print(f"Error deleting key: {e}")
        return False


def get_key(key: str) -> Any:
    try:
        ref = db.reference(key)
        return ref.get()
    except Exception as e:
        print(f"Error getting key: {e}")
        return None


def listen_to_changes(key: str, callback: Callable):
    try:
        ref = db.reference(key)
        ref.listen(callback)
    except Exception as e:
        print(f"Error setting up listener: {e}")


def update_agent_state(round_id: int, uuid: str, agent_dict: dict) -> None:
    """Update the agent state in firebase."""
    root_key = f"rounds/{round_id}/agents/{uuid}"
    for key, value in agent_dict.items():
        update_key(f"{root_key}/{key}", value)


def update_current_pairing(round_id: int, agent_pairs: list[tuple[str, str]]) -> None:
    """Update the current pairing in firebase."""
    key = f"rounds/{round_id}/current_pairing"
    update_key(key, agent_pairs)


def update_current_round_state(
    round_id: int | None,
    current_agents: list[str] | None,
    player_red_messages: list[dict] | None,
    player_blue_messages: list[dict] | None,
    agents_complete: bool | None,
) -> None:
    """Update the current pairing in firebase."""
    root_key = "current_state"
    if round_id is not None:
        update_key(f"{root_key}/round_number", round_id)
    if current_agents is not None:
        update_key(f"{root_key}/current_agents", current_agents)
    if player_red_messages is not None:
        update_key(f"{root_key}/round_state/player_red/messages", player_red_messages)
    if player_blue_messages is not None:
        update_key(f"{root_key}/round_state/player_blue/messages", player_blue_messages)
    if agents_complete is not None:
        update_key(f"{root_key}/round_state/agents_complete", agents_complete)


def listen_to_player_red(callback: Callable):
    listen_to_changes("current_state/round_state/player_red/", callback)


def listen_to_player_blue(callback: Callable):
    listen_to_changes("current_state/round_state/player_blue/", callback)


def listen_to_round_state(callback: Callable):
    listen_to_changes("current_state/round_state/", callback)


def get_round_state() -> dict:
    return get_key("current_state/round_state")


# /state
# {
#  roundNumber: 3,
#  roundState: {
#    player1: {
#      choose: 'gary'
#      messages: [{}, {}]
#      doneTalking: false
#    },
#    player2: ...
#    agentsCompleted: false
#  }
