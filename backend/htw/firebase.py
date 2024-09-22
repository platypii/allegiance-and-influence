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
