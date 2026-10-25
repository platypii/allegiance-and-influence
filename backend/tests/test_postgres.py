"""Opt-in integration suite: real PostgreSQL, isolated schemas, no live model calls."""

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
import test_game as game_checks
import test_runtime as runtime_checks
import test_solo as solo_checks
from fastapi.testclient import TestClient
from game.app import create_app
from game.core import GameError
from game.models import CreateGame
from game.postgres import PostgresStore
from game.store import Store


@pytest.fixture
def postgres(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration checks")
    import psycopg
    from psycopg.conninfo import make_conninfo

    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')
        scoped = make_conninfo(url, options=f"-c search_path={schema}")
        monkeypatch.setenv("DATABASE_URL", scoped)
        stores = []

        def factory(_path=None, characters=None, *args, **kwargs):
            store = PostgresStore(scoped, characters or game_checks.CHARACTERS, *args, **kwargs)
            stores.append(store)
            return store

        try:
            yield scoped, factory
        finally:
            for store in stores:
                store.close()
            admin.execute(f'DROP SCHEMA "{schema}" CASCADE')


@pytest.mark.parametrize(
    "check",
    [
        game_checks.test_duplicate_command_is_safe_and_stale_command_is_rejected,
        game_checks.test_private_messages_seat_ownership_and_game_isolation,
        game_checks.test_websocket_initial_update_reconnect_and_privacy,
    ],
)
def test_http_and_websocket_contracts(postgres, check):
    with TestClient(create_app()) as client:
        assert isinstance(client.app.state.store, PostgresStore)
        check(client)


@pytest.mark.parametrize(
    "check",
    [
        solo_checks.test_one_human_finishes_two_rounds_and_blue_cannot_be_claimed,
        solo_checks.test_selected_model_writes_arguments_character_keeps_own_model,
    ],
)
def test_solo_and_mixed_models(postgres, monkeypatch, tmp_path, check):
    monkeypatch.setattr(solo_checks, "create_app", lambda _path, **kwargs: create_app(**kwargs))
    check(tmp_path)


@pytest.mark.parametrize(
    "check",
    [
        runtime_checks.test_provider_result_commits_once_and_gets_only_own_observation,
        runtime_checks.test_transient_failure_retries_with_separate_budget_charges,
        runtime_checks.test_timeout_discards_late_result_and_retains_reservation,
        runtime_checks.test_cancel_during_call_then_retry_accepts_only_new_request,
        runtime_checks.test_concurrency_and_shared_game_budget,
        runtime_checks.test_declared_usage_violation_blocks_subsequent_calls,
    ],
)
def test_durable_runtime(postgres, monkeypatch, tmp_path, check):
    monkeypatch.setattr(runtime_checks, "Store", postgres[1])
    check(tmp_path)


def test_restart_retains_seats_replay_and_interrupted_charges(postgres, monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_checks, "Store", postgres[1])
    provider = runtime_checks.FakeProvider()
    store, game, _runtime = runtime_checks.setup(tmp_path, provider)
    state, actor = runtime_checks.send(store, game, text="persuasion")
    request_id = state["conversations"][actor]["work"]["request_id"]
    store.reserve_attempt(request_id)
    before = store.replay(game["id"], actor)
    store.close()
    with TestClient(create_app(provider=provider)) as client:
        recovered = client.app.state.store
        assert recovered.actor(game["id"], game_checks.RED) == actor
        assert recovered.replay(game["id"], actor)[:-1] == before
        assert recovered.load(game["id"])["conversations"][actor]["work"]["status"] == "interrupted"
        attempt = recovered.runtime_report(game["id"], actor)["attempts"][0]
        assert attempt["status"] == "interrupted" and attempt["charged_cost"] == 5
        assert provider.calls == 0


def test_single_owner_releases_on_shutdown_and_failed_initialization(postgres, monkeypatch):
    store = postgres[1]()
    with pytest.raises(RuntimeError, match="active game server"):
        postgres[1]()
    store.close()
    original = PostgresStore.initialize
    monkeypatch.setattr(PostgresStore, "initialize", lambda _self: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        postgres[1]()
    monkeypatch.setattr(PostgresStore, "initialize", original)
    postgres[1]().close()


def test_rollback_and_concurrent_seat_claims(postgres, monkeypatch):
    store = postgres[1]()
    game = store.create(CreateGame().model_dump())
    save = store._save

    def fail_after_save(*args):
        save(*args)
        raise RuntimeError("injected after snapshot and journal write")

    monkeypatch.setattr(store, "_save", fail_after_save)
    with pytest.raises(RuntimeError, match="injected"):
        store.join(game["id"], "player_red", game_checks.RED)
    assert store.load(game["id"]) == game
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM seats").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM events").fetchone()[0] == 1
    monkeypatch.setattr(store, "_save", save)

    def claim(i):
        try:
            store.join(game["id"], "player_red", str(i) * 48)
            return "joined"
        except GameError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(claim, range(8)))
    assert results.count("joined") == 1
    assert store.load(game["id"])["version"] == 1


def test_concurrent_reservations_do_not_overspend(postgres, monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_checks, "Store", postgres[1])
    policy = runtime_checks.config(call_limit=1, cost_limit_microusd=5)
    store, game, _runtime = runtime_checks.setup(tmp_path, runtime_checks.FakeProvider(), policy)
    ids = []
    for token in [game_checks.RED, game_checks.BLUE]:
        state, actor = runtime_checks.send(store, game, token, text="hello")
        ids.append(state["conversations"][actor]["work"]["request_id"])

    def reserve(request_id):
        try:
            return store.reserve_attempt(request_id)
        except GameError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, ids))
    assert results.count(1) == 1 and results.count("budget_exhausted") == 1


def test_explicit_local_path_ignores_hosted_environment(postgres, tmp_path):
    with TestClient(create_app(tmp_path / "isolated.db")) as client:
        assert type(client.app.state.store) is Store
        assert client.get("/api/health").status_code == 200


def test_lost_session_does_not_reconnect_or_fall_back(postgres):
    import psycopg

    store = postgres[1]()
    game = store.create(CreateGame().model_dump())
    store._db.close()  # Model a dropped connection after ownership was acquired.
    with pytest.raises(psycopg.OperationalError):
        store.load(game["id"])
    recovered = postgres[1]()
    assert recovered.load(game["id"]) == game


def test_production_launcher_serves_assets_and_preserves_game(postgres, tmp_path):
    import socket
    import subprocess
    import time
    from pathlib import Path

    import httpx

    root = Path(__file__).resolve().parents[2]
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = dict(os.environ, DATABASE_URL=postgres[0], PORT=str(port))
    log_path = tmp_path / "server.log"

    def start():
        with log_path.open("ab") as log:
            process = subprocess.Popen(
                ["bash", "scripts/replit-start.sh"], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT
            )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(log_path.read_text())
            try:
                if httpx.get(f"http://127.0.0.1:{port}/api/health").status_code == 200:
                    return process
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        process.terminate()
        process.wait(timeout=5)
        pytest.fail("Production launcher did not become healthy: " + log_path.read_text())

    def stop(process):
        process.terminate()
        process.wait(timeout=10)

    process = start()
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}") as client:
            assert client.get("/").status_code == 200
            result = client.post("/api/games", json={})
            assert result.status_code == 201
            game = result.json()
    finally:
        stop(process)
    process = start()
    try:
        result = httpx.get(f"http://127.0.0.1:{port}/api/games/{game['id']}")
        assert result.status_code == 200 and result.json() == game
    finally:
        stop(process)
    assert "ERROR:" not in log_path.read_text()


def test_neon_transaction_pooler_rejected_before_connecting(postgres):
    with pytest.raises(ValueError, match="direct PostgreSQL URL"):
        PostgresStore("postgresql://example-pooler.invalid/game", game_checks.CHARACTERS)
