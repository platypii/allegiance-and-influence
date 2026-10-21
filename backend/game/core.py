"""Pure state transitions for the scripted baseline. No I/O or model calls."""

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
    return {seat: {"target": None, "messages": [], "done": False} for seat in SEATS}


def new_game(game_id: str, config: dict, characters: list[dict]) -> dict:
    selected = random.Random(config["seed"]).sample(characters, config["num_agents"])
    return {
        "schema_version": "1",
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
        count = sum(m["name"] == seat for m in chat["messages"])
        if count >= 2:
            agent["side"] = SIDES[seat]
            result = f"{agent['Character']} joined {seat.removeprefix('player_').title()}."
        else:
            result = f"{agent['Character']} kept their allegiance. Two messages recruit in this demo."
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
        elif kind in {"message", "done"}:
            require(
                state["phase"] == "conversing", "wrong_phase", "Wait until both players choose a character."
            )
            require(not chat["done"], "conversation_done", "Your conversation has ended.")
            if kind == "message":
                text = command["text"].strip()
                require(bool(text), "empty_message", "Write a message first.")
                count = sum(m["name"] == actor for m in chat["messages"])
                require(count < 5, "message_limit", "Five messages is the limit. Finish your conversation.")
                chat["messages"].append({"name": actor, "content": text})
                reply = (
                    "Tell me more about how we would work together."
                    if count == 0
                    else "You have made your case. I will join your faction when this round ends."
                )
                chat["messages"].append({"name": chat["target"], "content": reply})
            else:
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
    result["you"] = actor
    return result
