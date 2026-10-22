import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .agent_contracts import RuntimePolicy, RuntimeReport
from .core import GameError, view
from .models import Command, CreateGame, GameView, JoinGame
from .providers import ScriptedProvider
from .runtime import AgentRuntime
from .store import Store

ROOT = Path(__file__).resolve().parents[2]


def create_app(db_path: Path | None = None, static_dir: Path | None = None, provider=None, policy=None):
    provider = provider or ScriptedProvider(float(os.environ.get("GAME_SCRIPTED_DELAY_MS", "0")) / 1000)
    policy = policy or RuntimePolicy()

    @asynccontextmanager
    async def lifespan(app):
        store.recover_jobs()
        yield
        await runtime.close()

    app = FastAPI(title="Allegiance & Influence", version="0.2.0", lifespan=lifespan)
    store = Store(
        db_path or Path(os.environ.get("GAME_DB", ROOT / "data/game.sqlite3")),
        json.loads((ROOT / "gameplay/characters.json").read_text()),
        identity=provider.identity,
        policy=policy,
    )
    app.state.store = store
    # Full snapshots in bounded queues: slow browsers converge to the latest state.
    subscribers: dict[str, set[asyncio.Queue]] = {}

    def publish(state):
        for queue in subscribers.get(state["id"], set()):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(state)

    runtime = AgentRuntime(store, provider, policy, publish)
    app.state.runtime = runtime

    def token_from(authorization):
        if not authorization or not authorization.startswith("Bearer "):
            raise GameError("unauthorized", "Join a player seat first.", 401)
        token = authorization[7:]
        if not 32 <= len(token) <= 128:
            raise GameError("invalid_token", "Invalid player key.", 401)
        return token

    @app.middleware("http")
    async def origin_guard(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return JSONResponse(
                {"error": {"code": "origin", "message": "Use the game server's own address."}},
                status_code=403,
            )
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(GameError)
    async def game_error(_request, error):
        return JSONResponse({"error": {"code": error.code, "message": str(error)}}, status_code=error.status)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "mode": "scripted", "schema_version": "2"}

    @app.post("/api/games", status_code=201, response_model=GameView)
    async def create(config: CreateGame):
        return view(store.create(config.model_dump()), None)

    @app.get("/api/games/{game_id}", response_model=GameView)
    async def get_game(game_id: str, authorization: str | None = Header(default=None)):
        actor = store.actor(game_id, token_from(authorization)) if authorization else None
        return view(store.load(game_id), actor)

    @app.post("/api/games/{game_id}/join", response_model=GameView)
    async def join(game_id: str, body: JoinGame, authorization: str | None = Header(default=None)):
        state = store.join(game_id, body.seat, token_from(authorization))
        publish(state)
        return view(state, body.seat)

    @app.post("/api/games/{game_id}/commands", response_model=GameView)
    async def command(game_id: str, body: Command, authorization: str | None = Header(default=None)):
        state, actor = store.apply(game_id, token_from(authorization), body.model_dump())
        publish(state)
        if body.kind in {"message", "retry"}:
            runtime.schedule(state, actor)
        elif body.kind == "cancel":
            work = state["conversations"][actor]["work"]
            # An idempotent replay returns current state, possibly a newer request/round.
            if work and work["status"] == "cancelled":
                runtime.cancel(work["request_id"])
        return view(state, actor)

    @app.get("/api/games/{game_id}/replay")
    async def replay(game_id: str, authorization: str | None = Header(default=None)):
        actor = store.actor(game_id, token_from(authorization))
        return {"schema_version": "2", "frames": store.replay(game_id, actor)}

    @app.get("/api/games/{game_id}/runtime", response_model=RuntimeReport)
    async def runtime_report(game_id: str, authorization: str | None = Header(default=None)):
        actor = store.actor(game_id, token_from(authorization))
        return store.runtime_report(game_id, actor)

    @app.websocket("/api/games/{game_id}/live")
    async def live(websocket: WebSocket, game_id: str):
        origin = websocket.headers.get("origin")
        if origin and urlsplit(origin).netloc != websocket.headers.get("host"):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        queue: asyncio.Queue = asyncio.Queue(maxsize=1)
        receive_task = update_task = None
        try:
            # Credentials travel in the first frame, never in a URL/access log.
            hello = await asyncio.wait_for(websocket.receive_json(), timeout=10)
            actor = (
                store.actor(game_id, token_from(hello.get("authorization")))
                if hello.get("authorization")
                else None
            )
            subscribers.setdefault(game_id, set()).add(queue)
            await websocket.send_json(view(store.load(game_id), actor))
            receive_task = asyncio.create_task(websocket.receive_text())
            while True:
                update_task = asyncio.create_task(queue.get())
                done, _ = await asyncio.wait({receive_task, update_task}, return_when=asyncio.FIRST_COMPLETED)
                if receive_task in done:
                    receive_task.result()
                    break
                await websocket.send_json(view(update_task.result(), actor))
        except WebSocketDisconnect:
            pass
        except (TimeoutError, GameError, ValueError, AttributeError):
            try:
                await websocket.close(code=1008)
            except (RuntimeError, WebSocketDisconnect):
                pass
        finally:
            for task in (receive_task, update_task):
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, WebSocketDisconnect):
                        pass
            group = subscribers.get(game_id)
            if group is not None:
                group.discard(queue)
                if not group:
                    subscribers.pop(game_id, None)

    static = static_dir or ROOT / "frontend/out"
    if static.is_dir():
        app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
    return app
