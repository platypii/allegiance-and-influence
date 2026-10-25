"""SQLite snapshots and an atomic command journal. One server process owns updates."""

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .agent_contracts import RuntimePolicy
from .core import GameError, new_game, transition, upgrade_state
from .jobs import Jobs
from .models import CreateGame, GameState
from .providers import ScriptedProvider


def encode(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Store(Jobs):
    def __init__(
        self,
        path: Path,
        characters: list[dict],
        identity=None,
        policy=None,
        routes=None,
        opponents=None,
    ):
        self.path, self.characters = path, characters
        self.identity = identity or ScriptedProvider.identity
        self.policy = policy or RuntimePolicy()
        self.routes = routes or {"*": self.identity.model_dump()}
        self.opponents = opponents or {"scripted": ScriptedProvider.identity.model_dump()}
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS games (id TEXT PRIMARY KEY, state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS seats (
                    game_id TEXT, seat TEXT, token_hash TEXT,
                    PRIMARY KEY(game_id, seat), UNIQUE(game_id, token_hash));
                CREATE TABLE IF NOT EXISTS events (
                    game_id TEXT, version INTEGER, actor TEXT, command_id TEXT,
                    command TEXT, state TEXT,
                    PRIMARY KEY(game_id, version), UNIQUE(game_id, command_id));
            """)

            self.init_jobs(db)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _load(self, db, game_id):
        row = db.execute("SELECT state FROM games WHERE id=?", (game_id,)).fetchone()
        if row is None:
            raise GameError("not_found", "Game not found. Create a new game.", 404)
        return upgrade_state(json.loads(row["state"]))

    def load(self, game_id):
        with self.connection() as db:
            return self._load(db, game_id)

    def _actor(self, db, game_id, token):
        row = db.execute(
            "SELECT seat FROM seats WHERE game_id=? AND token_hash=?", (game_id, digest(token))
        ).fetchone()
        if row is None:
            raise GameError("unauthorized", "This player key does not belong to this game.", 401)
        return row["seat"]

    def actor(self, game_id, token):
        with self.connection() as db:
            return self._actor(db, game_id, token)

    def _save(self, db, state, actor, command):
        GameState.model_validate(state)
        encoded = encode(state)
        db.execute("UPDATE games SET state=? WHERE id=?", (encoded, state["id"]))
        db.execute(
            "INSERT INTO events VALUES(?,?,?,?,?,?)",
            (
                state["id"],
                state["version"],
                actor,
                command["command_id"],
                encode(command),
                encoded,
            ),
        )

    def create(self, config, *, pair=None):
        # pair is internal experiment setup, never accepted by the public API.
        config = CreateGame.model_validate(config).model_dump()
        profile = config["opponent_profile"]
        if profile is not None and profile not in self.opponents:
            raise GameError("unknown_opponent", "Choose one of the configured opponent models.", 422)
        if pair and profile:
            raise ValueError("Pair experiments cannot also have a solo opponent")
        state = new_game(secrets.token_hex(16), config, self.characters)
        routes = dict(self.routes)
        if profile:
            routes["@opponent"] = self.opponents[profile]
            state["opponent"] = {"model": routes["@opponent"]["model"], "work": None, "error": None}
            state["players"]["player_blue"] = True
        if self.identity.provider != "scripted":
            state["mode"], state["rules_version"] = "model", "persuasion-v1"
        peers = {}
        if pair:
            if config["num_agents"] != 2 or config["num_rounds"] != 1 or len(set(pair)) != 2:
                raise ValueError("Pair experiments require two distinct characters and one round")
            by_id = {c["UID"]: c for c in self.characters}
            state["agents"] = [{**by_id[uid], "side": side} for uid, side in zip(pair, [-1, 1])]
            peers = dict(zip(["player_red", "player_blue"], state["agents"]))
        GameState.model_validate(state)
        with self.connection() as db:
            db.execute("INSERT INTO games VALUES(?,?)", (state["id"], encode(state)))
            db.execute(
                "INSERT INTO runtime_games VALUES(?,?,?)",
                (state["id"], encode(self.identity.model_dump()), encode(self.policy.model_dump())),
            )
            db.execute(
                "INSERT INTO runtime_context VALUES(?,?,?)",
                (state["id"], encode(routes), encode(peers)),
            )
            db.execute(
                "INSERT INTO events VALUES(?,?,?,?,?,?)",
                (
                    state["id"],
                    0,
                    None,
                    "created",
                    encode({"kind": "create"}),
                    encode(state),
                ),
            )
        return state

    def join(self, game_id, seat, token):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._load(db, game_id)
            existing = db.execute(
                "SELECT seat FROM seats WHERE game_id=? AND token_hash=?", (game_id, digest(token))
            ).fetchone()
            if existing:
                if existing["seat"] != seat:
                    raise GameError("already_joined", "This player key already owns another seat.")
                return state
            command = {"kind": "join", "command_id": "join_" + seat}
            state = transition(state, seat, command)
            db.execute("INSERT INTO seats VALUES(?,?,?)", (game_id, seat, digest(token)))
            self._save(db, state, seat, command)
        return state

    def apply(self, game_id, token, command):
        return self._apply(game_id, token, command)

    def apply_opponent(self, game_id, command):
        return self._apply(game_id, None, command, opponent=True)[0]

    def _apply(self, game_id, token, command, *, opponent=False):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._load(db, game_id)
            if opponent:
                if not state.get("opponent"):
                    raise GameError("not_solo", "This game has no model opponent.")
                actor = "player_blue"
            else:
                actor = self._actor(db, game_id, token)
            old = db.execute(
                "SELECT actor, command FROM events WHERE game_id=? AND command_id=?",
                (game_id, command["command_id"]),
            ).fetchone()
            if old:
                if old["actor"] != actor or old["command"] != encode(command):
                    raise GameError("id_conflict", "This command ID was already used for another action.")
                return state, actor
            if command["expected_version"] != state["version"]:
                raise GameError("stale_version", "The game changed. Review the board and try again.")
            state = transition(state, actor, command)
            if command["kind"] in {"message", "retry"}:
                self.attach_job(db, state, actor)
            elif command["kind"] == "cancel":
                request_id = state["conversations"][actor]["work"]["request_id"]
                db.execute(
                    "UPDATE agent_jobs SET status='cancelled',error='cancelled' WHERE id=?",
                    (request_id,),
                )
                db.execute(
                    "UPDATE agent_attempts SET status='cancelled' WHERE request_id=? AND status='running'",
                    (request_id,),
                )
            self._save(db, state, actor, command)
        return state, actor

    def replay(self, game_id, actor):
        from .core import view

        with self.connection() as db:
            rows = db.execute(
                "SELECT version, state FROM events WHERE game_id=? ORDER BY version", (game_id,)
            ).fetchall()
        return [view(upgrade_state(json.loads(row["state"])), actor) for row in rows]
