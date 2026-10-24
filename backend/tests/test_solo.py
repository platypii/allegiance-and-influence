import json
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from game.agent_contracts import RuntimePolicy
from game.app import create_app
from game.model_config import ModelConfig
from game.models import CreateGame
from game.openrouter import CharacterRouter
from game.opponent import complete_argument, queue_argument
from game.providers import ProviderFailure, ScriptedProvider
from game.store import Store
from test_game import BLUE, CHARACTERS, RED, auth
from test_openrouter import profile, response


def drain(client):
    client.portal.call(client.app.state.opponent.drain)
    client.portal.call(client.app.state.runtime.drain)


def get(client, game_id):
    return client.get(f"/api/games/{game_id}", headers=auth(RED)).json()


def start(client, profile_name="scripted", rounds=1):
    result = client.post("/api/games", json={"opponent_profile": profile_name, "num_rounds": rounds})
    assert result.status_code == 201, result.text
    game_id = result.json()["id"]
    result = client.post(f"/api/games/{game_id}/join", json={"seat": "player_red"}, headers=auth(RED))
    assert result.status_code == 200
    return get(client, game_id)


def command(client, game_id, kind, **fields):
    state = get(client, game_id)
    body = {"command_id": uuid.uuid4().hex, "expected_version": state["version"], "kind": kind, **fields}
    result = client.post(f"/api/games/{game_id}/commands", json=body, headers=auth(RED))
    assert result.status_code == 200, result.text
    drain(client)
    return get(client, game_id)


def test_one_human_finishes_two_rounds_and_blue_cannot_be_claimed(tmp_path):
    with TestClient(create_app(tmp_path / "solo.db")) as client:
        game = start(client, rounds=2)
        game_id = game["id"]
        assert game["players"] == {"player_red": True, "player_blue": True}
        assert game["phase"] == "selecting"
        assert (
            client.post(
                f"/api/games/{game_id}/join", json={"seat": "player_blue"}, headers=auth(BLUE)
            ).status_code
            == 409
        )
        for round_number in [1, 2]:
            game = command(client, game_id, "select", target=game["agents"][0]["UID"])
            assert game["conversations"]["player_blue"]["done"]
            assert game["conversations"]["player_blue"]["messages"] == []
            assert game["opponent"]["error"] is None
            assert (
                game["conversations"]["player_blue"]["target"]
                != game["conversations"]["player_red"]["target"]
            )
            game = command(client, game_id, "done")
            assert game["round_number"] == round_number
            if round_number == 1:
                game = command(client, game_id, "advance")
        assert game["phase"] == "finished" and game["winner"] == "player_blue"
        replay = client.get(f"/api/games/{game_id}/replay", headers=auth(RED)).json()["frames"]
        assert all(not f["conversations"]["player_blue"]["messages"] for f in replay)
        with client.app.state.store.connection() as db:
            assert db.execute("SELECT count(*) FROM agent_attempts").fetchone()[0] == 8


def test_selected_model_writes_arguments_character_keeps_own_model(tmp_path):
    calls = []

    def handler(req):
        body = json.loads(req.content)
        calls.append(body)
        brain = "You are the Blue player" in body["messages"][0]["content"]
        assert body["model"] == ("test/model-b" if brain else "test/model-a")
        # An opponent claiming it joins must not recruit a character that refused.
        return httpx.Response(200, json=response(body["model"], join=brain))

    config = ModelConfig(default_profile="a", profiles={"a": profile(), "b": profile("test/model-b")})
    router = CharacterRouter(config, "fixture-secret", httpx.MockTransport(handler))
    policy = RuntimePolicy(cost_limit_microusd=300000, token_limit=300000)
    with TestClient(create_app(tmp_path / "models.db", provider=router, policy=policy)) as client:
        options = client.get("/api/options").json()
        assert options["opponents"][1]["profile"] == "b"
        assert "fixture-secret" not in json.dumps(options)
        game = start(client, "b")
        assert game["opponent"]["model"] == "test/model-b"
        game = command(client, game["id"], "select", target=game["agents"][0]["UID"])
        game = command(client, game["id"], "done")
        assert game["phase"] == "finished" and game["scores"]["player_blue"] == 0
        assert len(calls) == 4
        report = client.app.state.store.runtime_report(game["id"], "player_blue")
        assert {a["identity"]["model"] for a in report["attempts"]} == {"test/model-a", "test/model-b"}
        assert sum(a["charged_cost"] for a in report["attempts"]) == 640


@pytest.mark.parametrize("failure", ["provider", "budget", "timeout"])
def test_opponent_failure_finishes_its_turn_without_blocking_human(tmp_path, failure):
    import asyncio

    class Failing(ScriptedProvider):
        async def generate(self, request):
            if failure == "provider":
                raise ProviderFailure("provider_unavailable")
            if failure == "timeout":
                await asyncio.sleep(1)
            return await super().generate(request)

    policy = RuntimePolicy(
        call_limit=1 if failure == "budget" else 10, timeout_seconds=0.02 if failure == "timeout" else 10
    )
    with TestClient(create_app(tmp_path / "fail.db", provider=Failing(), policy=policy)) as client:
        game = start(client)
        game = command(client, game["id"], "select", target=game["agents"][0]["UID"])
        assert game["conversations"]["player_blue"]["done"]
        assert (
            game["opponent"]["error"]
            == {"provider": "provider_unavailable", "budget": "budget_exhausted", "timeout": "timeout"}[
                failure
            ]
        )
        game = command(client, game["id"], "done")
        assert game["phase"] == "finished"


def test_unknown_profile_does_not_create_a_game(tmp_path):
    with TestClient(create_app(tmp_path / "invalid.db")) as client:
        result = client.post("/api/games", json={"opponent_profile": "vendor/arbitrary-model"})
        assert result.status_code == 422
        with client.app.state.store.connection() as db:
            assert db.execute("SELECT count(*) FROM games").fetchone()[0] == 0


def pending_solo(path):
    store = Store(path, CHARACTERS)
    game = store.create(CreateGame(opponent_profile="scripted", num_rounds=1).model_dump())
    game = store.join(game["id"], "player_red", RED)
    game, _ = store.apply(
        game["id"],
        RED,
        {
            "kind": "select",
            "target": game["agents"][0]["UID"],
            "expected_version": game["version"],
            "command_id": "red_select_pending",
        },
    )
    game = store.apply_opponent(
        game["id"],
        {
            "kind": "select",
            "target": game["agents"][1]["UID"],
            "expected_version": game["version"],
            "command_id": "blue_select_pending",
        },
    )
    game, _ = store.apply(
        game["id"],
        RED,
        {
            "kind": "message",
            "text": "RED_PRIVATE_SECRET",
            "expected_version": game["version"],
            "command_id": "red_private_message",
        },
    )
    game = queue_argument(store, game["id"])
    return store, game


def test_restart_interrupts_opponent_without_reissuing_and_preserves_privacy(tmp_path):
    path = tmp_path / "restart.db"
    store, game = pending_solo(path)
    job = store.job(game["opponent"]["work"]["request_id"])
    assert "RED_PRIVATE_SECRET" not in job["request"]
    with TestClient(create_app(path)) as client:
        drain(client)
        updated = get(client, game["id"])
        assert updated["opponent"]["error"] == "server_restarted"
        assert updated["conversations"]["player_blue"]["done"]
        updated = command(client, game["id"], "done")
        assert updated["phase"] == "finished"
        with store.connection() as db:
            assert db.execute("SELECT count(*) FROM agent_attempts").fetchone()[0] == 0


def test_stale_opponent_completion_cannot_append_a_message(tmp_path):
    store, game = pending_solo(tmp_path / "stale.db")
    request = json.loads(store.job(game["opponent"]["work"]["request_id"])["request"])
    request["round_number"] += 1
    assert (
        complete_argument(game, request, "succeeded", {"dialogue": "late", "join_opponent": True}, None)
        is None
    )


def test_v3_multiplayer_save_projects_to_v4_without_becoming_solo(tmp_path):
    store = Store(tmp_path / "old.db", CHARACTERS)
    state = store.create(CreateGame().model_dump())
    state["schema_version"] = "3"
    state.pop("opponent")
    state["config"].pop("opponent_profile")
    with store.connection() as db:
        db.execute("UPDATE games SET state=? WHERE id=?", (json.dumps(state), state["id"]))
    restored = store.load(state["id"])
    assert restored["schema_version"] == "4" and restored["opponent"] is None
    assert restored["config"]["opponent_profile"] is None and restored["version"] == 0


def test_changed_opponent_identity_fails_without_substituting_or_calling(tmp_path):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json=response())

    config = ModelConfig(default_profile="a", profiles={"a": profile(), "b": profile("test/model-b")})
    router = CharacterRouter(config, "fixture-key", httpx.MockTransport(handler))
    with TestClient(create_app(tmp_path / "pin.db", provider=router)) as client:
        game = start(client, "b")
        router.opponent_profiles["b"].identity = router.opponent_profiles["b"].identity.model_copy(
            update={"prompt_version": "changed-after-create"}
        )
        game = command(client, game["id"], "select", target=game["agents"][0]["UID"])
        assert game["opponent"]["error"] == "provider_changed"
        assert game["conversations"]["player_blue"]["done"]
        assert calls == []


def test_argument_completion_atomically_queues_character_reply_once(tmp_path):
    store, game = pending_solo(tmp_path / "atomic.db")
    request_id = game["opponent"]["work"]["request_id"]
    result = {
        "decision": {"dialogue": "A concrete plan for Blue.", "join_opponent": True},
        "usage": {"input_tokens": 0, "output_tokens": 0, "cost_microusd": 0},
    }
    updated = store.finish_job(request_id, "succeeded", result=result)
    chat = updated["conversations"]["player_blue"]
    assert chat["messages"][-1] == {"name": "player_blue", "content": "A concrete plan for Blue."}
    assert chat["join_opponent"] is False
    assert store.job(chat["work"]["request_id"])["status"] == "queued"
    assert store.finish_job(request_id, "succeeded", result=result) is None
    assert store.load(game["id"])["version"] == updated["version"]
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM agent_jobs").fetchone()[0] == 3
