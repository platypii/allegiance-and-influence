"""Pure game transitions. Provider work is committed separately by request identity."""

import hashlib
import random
from copy import deepcopy

SEATS = ("player_red", "player_blue")
SIDES = {"player_red": -1, "player_blue": 1}
RULES_VERSION = "scripted-v1"


class GameError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        super().__init__(message)
        self.code, self.status = code, status


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise GameError(code, message)


def conversations() -> dict:
    return {
        seat: {"target": None, "messages": [], "done": False, "join_opponent": False, "work": None}
        for seat in SEATS
    }


def new_game(game_id: str, config: dict, characters: list[dict]) -> dict:
    selected = random.Random(config["seed"]).sample(characters, config["num_agents"])
    return {
        "schema_version": "3",
        "rules_version": RULES_VERSION,
        "id": game_id,
        "version": 0,
        "config": config,
        "mode": "scripted",
        "phase": "lobby",
        "round_number": 1,
        "players": {seat: False for seat in SEATS},
        "agents": [{**c, "side": 0} for c in selected],
        "conversations": conversations(),
        "pairings": [],
        "history": [],
        "scores": {seat: 0 for seat in SEATS},
        "winner": None,
    }


def resolve_round(state: dict) -> None:
    by_id = {agent["UID"]: agent for agent in state["agents"]}
    summaries = []
    for seat, chat in state["conversations"].items():
        agent = by_id[chat["target"]]
        if chat["join_opponent"]:
            agent["side"] = SIDES[seat]
            result = f"{agent['Character']} joined {seat.removeprefix('player_').title()}."
        else:
            result = f"{agent['Character']} kept their allegiance."
        summaries.append({"pair": [chat["target"], seat], "text": result})
    # Resolve AI pairs from the same pre-resolution snapshot, without order effects.
    initial_sides = {uid: agent["side"] for uid, agent in by_id.items()}
    for pair in state["pairings"]:
        if any(uid in SEATS for uid in pair):
            continue
        left, right = [by_id[uid] for uid in pair]
        a, b = [initial_sides[uid] for uid in pair]
        if a != 0 and b == 0:
            right["side"] = a
            text = f"{left['Character']} persuaded {right['Character']} to join their faction."
        elif b != 0 and a == 0:
            left["side"] = b
            text = f"{right['Character']} persuaded {left['Character']} to join their faction."
        else:
            text = "They exchanged ideas and kept their allegiances."
        summaries.append({"pair": pair, "text": text})
    state["scores"] = {seat: sum(a["side"] == side for a in state["agents"]) for seat, side in SIDES.items()}
    state["history"].append(
        {
            "round_number": state["round_number"],
            "summaries": summaries,
            "scores": deepcopy(state["scores"]),
        }
    )
    if state["round_number"] == state["config"]["num_rounds"]:
        state["phase"] = "finished"
        red, blue = (state["scores"][s] for s in SEATS)
        state["winner"] = "tie" if red == blue else SEATS[0 if red > blue else 1]
    else:
        state["phase"] = "round_complete"


def transition(previous: dict, actor: str, command: dict) -> dict:
    state = deepcopy(previous)
    require(actor in SEATS, "invalid_seat", "Choose a valid player seat.")
    kind = command["kind"]
    if kind == "join":
        require(state["phase"] == "lobby", "game_started", "The game has already started.")
        require(not state["players"][actor], "seat_taken", "That player seat is occupied.")
        state["players"][actor] = True
        if all(state["players"].values()):
            state["phase"] = "selecting"
    else:
        require(state["players"][actor], "not_joined", "Join a player seat first.")
        chat = state["conversations"][actor]
        if kind == "select":
            require(state["phase"] == "selecting", "wrong_phase", "It is not time to choose a character.")
            require(chat["target"] is None, "already_selected", "You already chose this round.")
            target = command["target"]
            agent = next((a for a in state["agents"] if a["UID"] == target), None)
            require(agent is not None, "unknown_target", "Choose a character on this board.")
            require(
                not any(c["target"] == target for c in state["conversations"].values()),
                "target_taken",
                "The other player already chose this character.",
            )
            chat["target"] = target
            chat["messages"].append(
                {
                    "name": target,
                    "content": f"I am {agent['Character']}. What would you like our alliance to stand for?",
                }
            )
            if all(c["target"] for c in state["conversations"].values()):
                chosen = {c["target"] for c in state["conversations"].values()}
                remaining = [a["UID"] for a in state["agents"] if a["UID"] not in chosen]
                random.Random(state["config"]["seed"] + state["round_number"]).shuffle(remaining)
                state["pairings"] = [[c["target"], s] for s, c in state["conversations"].items()]
                state["pairings"] += [remaining[i : i + 2] for i in range(0, len(remaining) - 1, 2)]
                state["phase"] = "conversing"
        elif kind in {"message", "done", "retry", "cancel"}:
            require(
                state["phase"] == "conversing", "wrong_phase", "Wait until both players choose a character."
            )
            require(not chat["done"], "conversation_done", "Your conversation has ended.")
            pending = chat["work"] and chat["work"]["status"] == "pending"
            if kind == "cancel":
                require(pending, "no_pending_work", "There is no reply to cancel.")
                chat["work"]["status"] = "cancelled"
                chat["work"]["error"] = "cancelled"
            elif kind == "retry":
                require(
                    chat["work"] and chat["work"]["status"] in {"failed", "cancelled", "interrupted"},
                    "not_retryable",
                    "There is no failed reply to retry.",
                )
                chat["work"] = pending_work(state, actor, command)
            elif kind == "message":
                require(not pending, "reply_pending", "Wait for the reply or cancel it first.")
                text = command["text"].strip()
                require(bool(text), "empty_message", "Write a message first.")
                count = sum(m["name"] == actor for m in chat["messages"])
                require(count < 5, "message_limit", "Five messages is the limit. Finish your conversation.")
                chat["messages"].append({"name": actor, "content": text})
                chat["work"] = pending_work(state, actor, command)
            else:
                require(not pending, "reply_pending", "Wait for the reply or cancel it first.")
                chat["done"] = True
                if all(c["done"] for c in state["conversations"].values()):
                    resolve_round(state)
        elif kind == "advance":
            require(state["phase"] == "round_complete", "wrong_phase", "This round is not ready to advance.")
            state["round_number"] += 1
            state["conversations"] = conversations()
            state["pairings"] = []
            state["phase"] = "selecting"
        else:
            raise GameError("unknown_command", "Unknown game command.", 422)
    state["version"] += 1
    return state


def view(state: dict, actor: str | None) -> dict:
    result = deepcopy(state)
    # Opponent dialogue is private. Public round summaries remain visible to all.
    for seat, chat in result["conversations"].items():
        if seat != actor:
            chat["messages"] = []
            chat["join_opponent"] = False
            chat["work"] = None
    result["you"] = actor
    return result


def pending_work(state: dict, actor: str, command: dict) -> dict:
    request_id = hashlib.sha256(f"{state['id']}:{actor}:{command['command_id']}".encode()).hexdigest()
    return {"request_id": request_id, "status": "pending", "error": None}


def upgrade_state(original: dict) -> dict:
    """Read old snapshots without rewriting historical events or inventing provider calls."""
    state = deepcopy(original)
    if state["schema_version"] == "1":
        state["schema_version"] = "3"
        for seat, chat in state["conversations"].items():
            chat["join_opponent"] = sum(m["name"] == seat for m in chat["messages"]) >= 2
            chat["work"] = None
    if state["schema_version"] == "2":
        state["schema_version"] = "3"
    return state


def complete_work(
    previous: dict,
    actor: str,
    request: dict,
    status: str,
    decision: dict | None = None,
    error: str | None = None,
) -> dict | None:
    state = deepcopy(previous)
    chat = state["conversations"][actor]
    if (
        state["phase"] != "conversing"
        or state["round_number"] != request["round_number"]
        or chat["target"] != request["character"]["UID"]
        or chat["done"]
        or not chat["work"]
        or chat["work"]["request_id"] != request["request_id"]
        or chat["work"]["status"] != "pending"
    ):
        return None
    if decision is not None:
        chat["messages"].append({"name": chat["target"], "content": decision["dialogue"]})
        chat["join_opponent"] = decision["join_opponent"]
    chat["work"] = {"request_id": request["request_id"], "status": status, "error": error}
    state["version"] += 1
    return state
