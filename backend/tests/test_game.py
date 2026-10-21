import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from game.app import create_app
from game.core import GameError, new_game, transition
from game.models import CreateGame, GameView
from game.store import Store

ROOT = Path(__file__).resolve().parents[2]
CHARACTERS = json.loads((ROOT / "gameplay/characters.json").read_text())
RED, BLUE = "r" * 48, "b" * 48


def auth(token):
    return {"Authorization": "Bearer " + token}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "game.db")) as test_client:
        yield test_client


def setup_game(client, rounds=1, agents=6):
    response = client.post("/api/games", json={"num_agents": agents, "num_rounds": rounds, "seed": 32})
    assert response.status_code == 201
    game = response.json()
    for seat, token in [("player_red", RED), ("player_blue", BLUE)]:
        response = client.post(f"/api/games/{game['id']}/join", json={"seat": seat}, headers=auth(token))
        assert response.status_code == 200
    return client.get(f"/api/games/{game['id']}", headers=auth(RED)).json()


def send(client, game_id, token, kind, **kwargs):
    game = client.get(f"/api/games/{game_id}", headers=auth(token)).json()
    body = {"kind": kind, "command_id": uuid.uuid4().hex, "expected_version": game["version"], **kwargs}
    return client.post(f"/api/games/{game_id}/commands", headers=auth(token), json=body)


def choose(client, game):
    for i, token in enumerate([RED, BLUE]):
        response = send(client, game["id"], token, "select", target=game["agents"][i]["UID"])
        assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize("rounds,agents", [(1, 2), (3, 6), (2, 5)])
def test_full_match_ties_score_and_completion(client, rounds, agents):
    game = setup_game(client, rounds, agents)
    for round_number in range(1, rounds + 1):
        game = choose(client, game)
        assert game["phase"] == "conversing"
        for token in [RED, BLUE]:
            for text in ["Let us work together", "We share a purpose"]:
                assert send(client, game["id"], token, "message", text=text).status_code == 200
            result = send(client, game["id"], token, "done")
            assert result.status_code == 200
        game = result.json()
        GameView.model_validate(game)
        assert game["round_number"] == round_number
        assert game["scores"] == {"player_red": 1, "player_blue": 1}
        assert len(game["history"]) == round_number
        if round_number < rounds:
            assert game["phase"] == "round_complete"
            game = send(client, game["id"], RED, "advance").json()
    assert game["phase"] == "finished"
    assert game["winner"] == "tie"
    assert send(client, game["id"], RED, "advance").status_code == 409


def test_final_round_winner_and_empty_conversations(client):
    game = choose(client, setup_game(client))
    for text in ["one", "two"]:
        send(client, game["id"], RED, "message", text=text)
    send(client, game["id"], RED, "done")
    result = send(client, game["id"], BLUE, "done").json()
    assert result["winner"] == "player_red"
    assert result["scores"] == {"player_red": 1, "player_blue": 0}


def test_same_target_and_invalid_phase_do_not_mutate_state(client):
    game = setup_game(client)
    assert send(client, game["id"], RED, "message", text="early").status_code == 409
    assert send(client, game["id"], RED, "select", target="unknown").status_code == 409
    target = game["agents"][0]["UID"]
    send(client, game["id"], RED, "select", target=target)
    response = send(client, game["id"], BLUE, "select", target=target)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "target_taken"
    state = client.get(f"/api/games/{game['id']}").json()
    assert state["version"] == game["version"] + 1
    assert state["conversations"]["player_blue"]["target"] is None


def test_duplicate_command_is_safe_and_stale_command_is_rejected(client):
    game = choose(client, setup_game(client))
    body = {
        "kind": "message",
        "command_id": uuid.uuid4().hex,
        "expected_version": game["version"],
        "text": "hello",
    }
    path = f"/api/games/{game['id']}/commands"
    first = client.post(path, headers=auth(RED), json=body)
    retry = client.post(path, headers=auth(RED), json=body)
    assert first.json() == retry.json()
    assert len(retry.json()["conversations"]["player_red"]["messages"]) == 3
    conflict = client.post(path, headers=auth(RED), json={**body, "text": "different"})
    assert conflict.json()["error"]["code"] == "id_conflict"
    stale = client.post(path, headers=auth(RED), json={**body, "command_id": uuid.uuid4().hex})
    assert stale.json()["error"]["code"] == "stale_version"


def test_private_messages_seat_ownership_and_game_isolation(client):
    game = choose(client, setup_game(client))
    send(client, game["id"], RED, "message", text="private red words")
    path = f"/api/games/{game['id']}"
    assert "private red words" not in client.get(path).text
    assert "private red words" not in client.get(path, headers=auth(BLUE)).text
    assert "private red words" in client.get(path, headers=auth(RED)).text
    taken = client.post(path + "/join", headers=auth("x" * 48), json={"seat": "player_red"})
    assert taken.status_code == 409
    assert client.post(path + "/join", headers=auth(RED), json={"seat": "player_red"}).status_code == 200
    assert client.get(path, headers=auth("x" * 48)).status_code == 401
    other = client.post("/api/games", json={}).json()
    assert client.get(f"/api/games/{other['id']}", headers=auth(RED)).status_code == 401
    assert client.get(path + "/replay").status_code == 401
    assert "private red words" not in client.get(path + "/replay", headers=auth(BLUE)).text
    assert "token" not in client.get(path + "/replay", headers=auth(RED)).text


def test_restart_and_replay_match_committed_state(tmp_path):
    db = tmp_path / "persist.db"
    with TestClient(create_app(db)) as client:
        game = choose(client, setup_game(client))
        send(client, game["id"], RED, "message", text="saved after restart")
        before = client.get(f"/api/games/{game['id']}", headers=auth(RED)).json()
    with TestClient(create_app(db)) as restarted:
        after = restarted.get(f"/api/games/{game['id']}", headers=auth(RED)).json()
        assert after == before
        frames = restarted.get(f"/api/games/{game['id']}/replay", headers=auth(RED)).json()["frames"]
        assert frames[-1] == after
        assert [f["version"] for f in frames] == list(range(after["version"] + 1))
        assert send(restarted, game["id"], RED, "done").status_code == 200


def test_websocket_initial_update_reconnect_and_privacy(client):
    game = setup_game(client)
    path = f"/api/games/{game['id']}/live"
    with client.websocket_connect(path) as socket:
        socket.send_json({"authorization": "Bearer " + BLUE})
        first = socket.receive_json()
        assert first["you"] == "player_blue"
        response = send(client, game["id"], RED, "select", target=game["agents"][0]["UID"])
        update = socket.receive_json()
        assert update["version"] == response.json()["version"]
        assert update["conversations"]["player_red"]["messages"] == []
    with client.websocket_connect(path) as socket:
        socket.send_json({})
        state = socket.receive_json()
        assert state["version"] == update["version"]
        assert state["you"] is None


@pytest.mark.parametrize(
    "payload", [{"num_agents": 1}, {"num_rounds": 0}, {"seed": -1}, {"provider": "live"}, {"num_agents": "6"}]
)
def test_configuration_rejects_invalid_input(client, payload):
    assert client.post("/api/games", json=payload).status_code == 422


def test_message_limits_and_unknown_fields(client):
    game = choose(client, setup_game(client))
    assert send(client, game["id"], RED, "message", text=" " * 2).status_code == 409
    assert send(client, game["id"], RED, "message", text="x" * 2001).status_code == 422
    assert send(client, game["id"], RED, "done", admin=True).status_code == 422
    for _ in range(5):
        assert send(client, game["id"], RED, "message", text="valid").status_code == 200
    assert send(client, game["id"], RED, "message", text="sixth").json()["error"]["code"] == "message_limit"
    send(client, game["id"], RED, "done")
    assert send(client, game["id"], RED, "message", text="late").status_code == 409


def test_cross_origin_write_rejected(client):
    assert (
        client.post("/api/games", json={}, headers={"Origin": "https://elsewhere.example"}).status_code == 403
    )


def test_concurrent_claims_and_choices_are_serialized(tmp_path):
    store = Store(tmp_path / "race.db", CHARACTERS)
    game = store.create(CreateGame().model_dump())

    def claim(token):
        try:
            store.join(game["id"], "player_red", token)
            return token
        except GameError:
            return None

    with ThreadPoolExecutor(2) as pool:
        winners = [token for token in pool.map(claim, [RED, BLUE]) if token]
    assert len(winners) == 1
    other_token = "z" * 48
    store.join(game["id"], "player_blue", other_token)
    state = store.load(game["id"])

    def select(token):
        try:
            store.apply(
                game["id"],
                token,
                {
                    "kind": "select",
                    "command_id": uuid.uuid4().hex,
                    "expected_version": state["version"],
                    "target": state["agents"][0]["UID"],
                },
            )
            return True
        except GameError:
            return False

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(select, [winners[0], other_token]))
    assert sum(results) == 1


def test_seeded_pairing_and_transition_leave_input_unchanged():
    config = CreateGame(num_agents=10).model_dump()
    original = new_game("fixed", config, CHARACTERS)
    assert original == new_game("fixed", config, CHARACTERS)
    state = transition(original, "player_red", {"kind": "join"})
    assert original["version"] == 0
    assert original["players"]["player_red"] is False
    state = transition(state, "player_blue", {"kind": "join"})
    for i, seat in enumerate(["player_red", "player_blue"]):
        state = transition(state, seat, {"kind": "select", "target": state["agents"][i]["UID"]})
    paired = [uid for pair in state["pairings"] for uid in pair]
    assert len(paired) == len(set(paired)) == 12
    assert state["pairings"][2:] != [
        [state["agents"][i]["UID"], state["agents"][i + 1]["UID"]] for i in range(2, 10, 2)
    ]
