"""SQLite snapshots and an atomic command journal. One server process owns updates."""

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .core import GameError, new_game, transition
from .models import GameState


def encode(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Store:
    def __init__(self, path: Path, characters: list[dict]):
        self.path, self.characters = path, characters
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
        return json.loads(row["state"])

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

    def create(self, config):
        state = new_game(secrets.token_hex(16), config, self.characters)
        GameState.model_validate(state)
        with self.connection() as db:
            db.execute("INSERT INTO games VALUES(?,?)", (state["id"], encode(state)))
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
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._load(db, game_id)
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
            self._save(db, state, actor, command)
        return state, actor

    def replay(self, game_id, actor):
        from .core import view

        with self.connection() as db:
            rows = db.execute(
                "SELECT version, state FROM events WHERE game_id=? ORDER BY version", (game_id,)
            ).fetchall()
        return [view(json.loads(row["state"]), actor) for row in rows]
