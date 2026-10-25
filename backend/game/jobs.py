"""Durable provider requests, per-attempt budget reservations, and atomic completion."""

import json
from time import time

from .agent_contracts import AgentRequest, ProviderResult
from .core import SIDES, GameError, complete_work


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class Jobs:
    def init_jobs(self, db):
        db.executescript("""
            CREATE TABLE IF NOT EXISTS runtime_games (
                game_id TEXT PRIMARY KEY, identity TEXT NOT NULL, policy TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS agent_jobs (
                id TEXT PRIMARY KEY, game_id TEXT NOT NULL, actor TEXT NOT NULL,
                request TEXT NOT NULL, status TEXT NOT NULL, error TEXT);
            CREATE TABLE IF NOT EXISTS agent_attempts (
                request_id TEXT, attempt BIGINT, status TEXT NOT NULL,
                charged_tokens BIGINT NOT NULL, charged_cost BIGINT NOT NULL,
                usage TEXT, latency_ms INTEGER, started_at DOUBLE PRECISION,
                PRIMARY KEY(request_id, attempt));
            CREATE TABLE IF NOT EXISTS runtime_context (
                game_id TEXT PRIMARY KEY, routes TEXT NOT NULL, peers TEXT NOT NULL);
        """)

        # Additive migration preserves existing requests and attempt accounting.
        for table, column in [("agent_jobs", "route"), ("agent_attempts", "receipt")]:
            self.add_column(db, table, column)

    def attach_job(self, db, state, actor):
        chat = state["conversations"][actor]
        work = chat["work"]
        context = db.execute("SELECT * FROM runtime_context WHERE game_id=?", (state["id"],)).fetchone()
        peers = json.loads(context["peers"]) if context else {}
        request = AgentRequest(
            request_id=work["request_id"],
            game_id=state["id"],
            round_number=state["round_number"],
            character=next(a for a in state["agents"] if a["UID"] == chat["target"]),
            opponent=actor,
            opponent_character=peers.get(actor),
            opponent_side=SIDES[actor],
            messages=chat["messages"],
        )
        db.execute(
            "INSERT INTO runtime_games VALUES(?,?,?) ON CONFLICT DO NOTHING",
            (
                state["id"],
                packed(self.identity.model_dump()),
                packed(self.policy.model_dump()),
            ),
        )
        # Legacy games keep their previously pinned provider; never relabel scripted saves.
        settings = db.execute("SELECT identity FROM runtime_games WHERE game_id=?", (state["id"],)).fetchone()
        identity = json.loads(settings["identity"])
        if not context and state["mode"] == "scripted" and identity["provider"] != "scripted":
            raise GameError("provider_changed", "Create a new game for the configured models.")
        routes = json.loads(context["routes"]) if context else {"*": identity}
        route = routes.get(chat["target"], routes["*"])
        db.execute(
            "INSERT INTO agent_jobs (id,game_id,actor,request,status,error,route) VALUES(?,?,?,?,?,?,?)",
            (
                work["request_id"],
                state["id"],
                actor,
                request.model_dump_json(by_alias=True),
                "queued",
                None,
                packed(route),
            ),
        )

    def job(self, request_id):
        with self.connection() as db:
            row = db.execute(
                "SELECT j.*, r.identity, r.policy FROM agent_jobs j JOIN runtime_games r "
                "ON r.game_id=j.game_id WHERE j.id=?",
                (request_id,),
            ).fetchone()
            return dict(row) if row else None

    def reserve_attempt(self, request_id):
        with self.connection() as db:
            self.begin_write(db)
            job = db.execute("SELECT * FROM agent_jobs WHERE id=?", (request_id,)).fetchone()
            if not job or job["status"] not in {"queued", "running"}:
                return None
            violated = db.execute(
                "SELECT 1 FROM agent_attempts a JOIN agent_jobs j ON a.request_id=j.id "
                "WHERE j.game_id=? AND a.status='usage_exceeded' LIMIT 1",
                (job["game_id"],),
            ).fetchone()
            if violated:
                raise GameError(
                    "provider_bounds_exceeded", "The provider exceeded its declared usage limits."
                )
            settings = db.execute("SELECT * FROM runtime_games WHERE game_id=?", (job["game_id"],)).fetchone()
            policy = json.loads(settings["policy"])
            identity = json.loads(job["route"] or settings["identity"])
            total = db.execute(
                "SELECT count(*) calls, coalesce(sum(a.charged_tokens),0) tokens, "
                "coalesce(sum(a.charged_cost),0) cost FROM agent_attempts a JOIN agent_jobs j "
                "ON a.request_id=j.id WHERE j.game_id=?",
                (job["game_id"],),
            ).fetchone()
            attempt = (
                db.execute(
                    "SELECT count(*) FROM agent_attempts WHERE request_id=?", (request_id,)
                ).fetchone()[0]
                + 1
            )
            tokens = identity["max_input_tokens"] + identity["max_output_tokens"]
            cost = identity["max_cost_microusd"]
            if (
                attempt > policy["max_attempts"]
                or total["calls"] + 1 > policy["call_limit"]
                or total["tokens"] + tokens > policy["token_limit"]
                or total["cost"] + cost > policy["cost_limit_microusd"]
            ):
                raise GameError("budget_exhausted", "The game has reached its agent budget.")
            db.execute(
                "INSERT INTO agent_attempts (request_id,attempt,status,charged_tokens,charged_cost,usage,latency_ms,started_at) VALUES(?,?,?,?,?,?,?,?)",
                (
                    request_id,
                    attempt,
                    "running",
                    tokens,
                    cost,
                    None,
                    None,
                    time(),
                ),
            )
            db.execute("UPDATE agent_jobs SET status='running' WHERE id=?", (request_id,))
            return attempt

    def record_attempt(self, request_id, attempt, status, latency_ms, usage=None, receipt=None):
        with self.connection() as db:
            self.begin_write(db)
            db.execute(
                "UPDATE agent_attempts SET receipt=? WHERE request_id=? AND attempt=? AND status='running'",
                (packed(receipt) if receipt else None, request_id, attempt),
            )
            # Only a successfully validated response releases unused reservation.
            if usage is not None and status == "succeeded":
                db.execute(
                    "UPDATE agent_attempts SET status=?, latency_ms=?, usage=?, charged_tokens=?, "
                    "charged_cost=? WHERE request_id=? AND attempt=? AND status='running'",
                    (
                        status,
                        latency_ms,
                        packed(usage),
                        usage["input_tokens"] + usage["output_tokens"],
                        usage["cost_microusd"],
                        request_id,
                        attempt,
                    ),
                )
            elif usage is not None:
                db.execute(
                    "UPDATE agent_attempts SET status=?, latency_ms=?, usage=?, "
                    "charged_tokens=CASE WHEN charged_tokens>? THEN charged_tokens ELSE ? END, "
                    "charged_cost=CASE WHEN charged_cost>? THEN charged_cost ELSE ? END "
                    "WHERE request_id=? AND attempt=? AND status='running'",
                    (
                        status,
                        latency_ms,
                        packed(usage),
                        usage["input_tokens"] + usage["output_tokens"],
                        usage["input_tokens"] + usage["output_tokens"],
                        usage["cost_microusd"],
                        usage["cost_microusd"],
                        request_id,
                        attempt,
                    ),
                )
            else:
                db.execute(
                    "UPDATE agent_attempts SET status=?, latency_ms=?, usage=? "
                    "WHERE request_id=? AND attempt=? AND status='running'",
                    (
                        status,
                        latency_ms,
                        packed(usage) if usage is not None else None,
                        request_id,
                        attempt,
                    ),
                )

    def finish_job(self, request_id, status, error=None, result=None):
        if (status == "succeeded") != (result is not None):
            raise ValueError("Only successful work may contain a validated provider result")
        if result is not None:
            result = ProviderResult.model_validate(result).model_dump()
        with self.connection() as db:
            self.begin_write(db)
            row = db.execute("SELECT * FROM agent_jobs WHERE id=?", (request_id,)).fetchone()
            if not row or row["status"] not in {"queued", "running"}:
                return None
            state = self._load(db, row["game_id"])
            request = json.loads(row["request"])
            if request.get("purpose") == "opponent_argument":
                from .opponent import complete_argument

                updated = complete_argument(
                    state, request, status, result["decision"] if result else None, error
                )
                if updated and result:
                    self.attach_job(db, updated, "player_blue")
            else:
                updated = complete_work(
                    state,
                    row["actor"],
                    request,
                    status,
                    result["decision"] if result else None,
                    error,
                )
            db.execute(
                "UPDATE agent_jobs SET status=?, error=? WHERE id=?",
                (
                    status if updated else "discarded",
                    error,
                    request_id,
                ),
            )
            if updated:
                self._save(
                    db,
                    updated,
                    row["actor"],
                    {
                        "kind": "agent_result",
                        "command_id": "agent_" + request_id,
                        "request_id": request_id,
                        "status": status,
                        "error": error,
                    },
                )
            return updated

    def recover_jobs(self):
        with self.connection() as db:
            pending = db.execute("SELECT id FROM agent_jobs WHERE status IN ('queued','running')").fetchall()
            db.execute("UPDATE agent_attempts SET status='interrupted' WHERE status='running'")
        for row in pending:
            self.finish_job(row["id"], "interrupted", "server_restarted")
        return len(pending)

    def runtime_report(self, game_id, actor):
        with self.connection() as db:
            settings = db.execute(
                "SELECT identity,policy FROM runtime_games WHERE game_id=?", (game_id,)
            ).fetchone()
            if not settings:
                return {"schema_version": "2", "identity": None, "policy": None, "attempts": []}
            rows = db.execute(
                "SELECT j.id request_id, a.attempt, a.status, a.charged_tokens, a.charged_cost, "
                "a.usage, a.latency_ms, a.receipt, j.route identity FROM agent_jobs j JOIN agent_attempts a "
                "ON j.id=a.request_id WHERE j.game_id=? AND j.actor=? ORDER BY a.started_at, a.attempt",
                (game_id, actor),
            ).fetchall()
        attempts = [
            {
                **dict(row),
                **{
                    key: json.loads(row[key]) if row[key] else None
                    for key in ["usage", "receipt", "identity"]
                },
            }
            for row in rows
        ]
        return {
            "schema_version": "2",
            "identity": json.loads(settings["identity"]),
            "policy": json.loads(settings["policy"]),
            "attempts": attempts,
        }
