"""One bounded Blue driver per solo game; provider work uses the shared durable runtime."""

import asyncio
import hashlib
import json
from copy import deepcopy

from .agent_contracts import AgentRequest
from .core import transition


def complete_argument(previous, request, status, decision, error):
    state = deepcopy(previous)
    opponent = state.get("opponent")
    chat = state["conversations"]["player_blue"]
    work = opponent and opponent["work"]
    if (
        not work
        or work["status"] != "pending"
        or work["request_id"] != request["request_id"]
        or state["phase"] != "conversing"
        or chat["done"]
        or state["round_number"] != request["round_number"]
        or chat["target"] != request["opponent_character"]["UID"]
    ):
        return None
    opponent["work"] = {"request_id": request["request_id"], "status": status, "error": error}
    opponent["error"] = error
    if decision:
        # Ignore the strategist's recruitment boolean. Only the character can accept.
        state = transition(
            state,
            "player_blue",
            {
                "kind": "message",
                "text": decision["dialogue"],
                "command_id": "reply_" + request["request_id"],
            },
        )
    else:
        state["version"] += 1
    return state


def queue_argument(store, game_id):
    with store.connection() as db:
        store.begin_write(db)
        state = store._load(db, game_id)
        opponent = state["opponent"]
        chat = state["conversations"]["player_blue"]
        if state["phase"] != "conversing" or chat["done"]:
            return state
        work = opponent["work"]
        if work and work["status"] == "pending":
            return state
        count = sum(m["name"] == "player_blue" for m in chat["messages"])
        request_id = hashlib.sha256(f"{game_id}:blue:{state['round_number']}:{count}".encode()).hexdigest()
        opponent["work"] = {"request_id": request_id, "status": "pending", "error": None}
        target = next(a for a in state["agents"] if a["UID"] == chat["target"])
        # Reuse the character shape with an explicit fictional player persona.
        persona = {
            **target,
            "UID": "player_blue",
            "Character": "Blue recruiter",
            "side": 1,
            "Description": "A fictional strategist recruiting allies into Blue.",
        }
        request = AgentRequest(
            purpose="opponent_argument",
            request_id=request_id,
            game_id=game_id,
            round_number=state["round_number"],
            character=persona,
            opponent="player_red",
            opponent_character=target,
            opponent_side=-1,
            messages=chat["messages"],
        )
        routes = json.loads(
            db.execute("SELECT routes FROM runtime_context WHERE game_id=?", (game_id,)).fetchone()[0]
        )
        db.execute(
            "INSERT INTO agent_jobs (id,game_id,actor,request,status,error,route) VALUES(?,?,?,?,?,?,?)",
            (
                request_id,
                game_id,
                "player_blue",
                request.model_dump_json(by_alias=True),
                "queued",
                None,
                json.dumps(routes["@opponent"]),
            ),
        )
        state["version"] += 1
        store._save(
            db,
            state,
            "player_blue",
            {"kind": "opponent_argument", "command_id": "opponent_" + request_id},
        )
        return state


class OpponentDriver:
    def __init__(self, store, runtime, publish):
        self.store, self.runtime, self.publish = store, runtime, publish
        self.tasks = {}
        self.closing = False

    def wake(self, state):
        if self.closing or not state.get("opponent") or state["id"] in self.tasks:
            return
        if state["phase"] == "selecting" and (
            not state["conversations"]["player_red"]["target"]
            or state["conversations"]["player_blue"]["target"]
        ):
            return
        if state["conversations"]["player_blue"]["done"]:
            return
        if state["phase"] not in {"selecting", "conversing"}:
            return
        task = asyncio.create_task(self.run(state["id"]))
        self.tasks[state["id"]] = task
        task.add_done_callback(lambda done: self.completed(state["id"], done))

    def completed(self, game_id, task):
        self.tasks.pop(game_id, None)
        if not task.cancelled() and task.exception():
            # Safe, visible terminal error instead of an unhandled driver exception.
            self.fail(game_id, "opponent_error")
        elif not task.cancelled():
            self.wake(self.store.load(game_id))

    def fail(self, game_id, error):
        with self.store.connection() as db:
            self.store.begin_write(db)
            state = self.store._load(db, game_id)
            if state["phase"] != "conversing" or state["conversations"]["player_blue"]["done"]:
                return
            state["opponent"]["error"] = error
            work = state["conversations"]["player_blue"]["work"]
            if work and work["status"] == "pending":
                return
            state = transition(state, "player_blue", {"kind": "done"})
            self.store._save(
                db,
                state,
                "player_blue",
                {
                    "kind": "opponent_stopped",
                    "command_id": f"opponent_stop_{state['round_number']}",
                    "error": error,
                },
            )
        self.publish(state)

    def command(self, state, kind, **fields):
        command = {
            "kind": kind,
            "expected_version": state["version"],
            "command_id": f"blue_{state['round_number']}_{kind}",
            **fields,
        }
        updated = self.store.apply_opponent(state["id"], command)
        self.publish(updated)

    async def run(self, game_id):
        # Two arguments + two character replies plus select/done. Never an open-ended agent loop.
        for _ in range(12):
            state = self.store.load(game_id)
            chat = state["conversations"]["player_blue"]
            if state["phase"] == "selecting":
                chosen = state["conversations"]["player_red"]["target"]
                if not chosen or chat["target"]:
                    return
                targets = sorted(
                    (a for a in state["agents"] if a["UID"] != chosen),
                    key=lambda a: (a["side"] == 1, a["UID"]),
                )
                self.command(state, "select", target=targets[0]["UID"])
                continue
            if state["phase"] != "conversing" or chat["done"]:
                return
            work = chat["work"]
            brain = state["opponent"]["work"]
            for current, is_brain in [(work, False), (brain, True)]:
                if current and current["status"] == "pending":
                    self.runtime.schedule(state, "player_blue", opponent=is_brain)
                    task = self.runtime.tasks.get(current["request_id"])
                    if task:
                        await asyncio.shield(task)
                    break
            else:
                failed = next(
                    (w for w in [work, brain] if w and w["status"] in {"failed", "cancelled", "interrupted"}),
                    None,
                )
                if failed:
                    self.fail(game_id, failed["error"] or failed["status"])
                    return
                if sum(m["name"] == "player_blue" for m in chat["messages"]) >= 2 or chat["join_opponent"]:
                    self.command(state, "done")
                    return
                self.publish(queue_argument(self.store, game_id))
        self.fail(game_id, "opponent_turn_limit")

    async def drain(self):
        while self.tasks:
            await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)

    async def close(self):
        self.closing = True
        for task in list(self.tasks.values()):
            task.cancel()
        await self.drain()
