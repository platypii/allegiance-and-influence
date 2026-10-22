import asyncio
import json
import uuid
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from game.agent_contracts import ProviderIdentity, RuntimePolicy
from game.app import create_app
from game.core import view
from game.models import CreateGame
from game.providers import RetryableProviderError, ScriptedProvider
from game.runtime import AgentRuntime
from game.store import Store

ROOT = Path(__file__).resolve().parents[2]
ROSTER = json.loads((ROOT / "gameplay/characters.json").read_text())
RED, BLUE = "r" * 48, "b" * 48


def config(**changes):
    return RuntimePolicy(**changes)


class FakeProvider:
    identity = ProviderIdentity(
        provider="fake",
        model="conformance",
        prompt_version="1",
        max_input_tokens=10,
        max_output_tokens=10,
        max_cost_microusd=5,
    )

    def __init__(self, behavior="ok", delay=0.0):
        self.behavior, self.delay = behavior, delay
        self.calls = 0
        self.active = 0
        self.peak = 0
        self.requests = []

    async def generate(self, request):
        self.calls += 1
        self.active += 1
        self.peak = max(self.peak, self.active)
        self.requests.append(request.model_dump(by_alias=True))
        try:
            try:
                await asyncio.sleep(self.delay)
            except asyncio.CancelledError:
                if self.behavior != "late":
                    raise
                await asyncio.sleep(0.02)
            if self.behavior == "transient" and self.calls == 1:
                raise RetryableProviderError("hidden provider details")
            if self.behavior == "always_transient":
                raise RetryableProviderError("hidden provider details")
            if self.behavior == "error":
                raise RuntimeError("credential=DO_NOT_EXPOSE")
            result = {
                "schema_version": "1",
                "decision": {"dialogue": "A bounded reply.", "join_opponent": True},
                "usage": {"input_tokens": 3, "output_tokens": 4, "cost_microusd": 2},
            }
            if self.behavior == "invalid":
                result["decision"]["side"] = -1
            if self.behavior == "bad_usage":
                result["usage"]["input_tokens"] = 1000
            if self.behavior == "blank":
                result["decision"]["dialogue"] = "   "
            return result
        finally:
            self.active -= 1


def setup(tmp_path, provider, policy=None):
    policy = policy or config(cost_limit_microusd=100)
    store = Store(tmp_path / "runtime.db", ROSTER, provider.identity, policy)
    game = store.create(CreateGame(num_rounds=2).model_dump())
    for seat, token in [("player_red", RED), ("player_blue", BLUE)]:
        game = store.join(game["id"], seat, token)
    for i, token in enumerate([RED, BLUE]):
        game, _ = store.apply(
            game["id"],
            token,
            {
                "kind": "select",
                "target": game["agents"][i]["UID"],
                "expected_version": game["version"],
                "command_id": uuid.uuid4().hex,
            },
        )
    return store, game, AgentRuntime(store, provider, policy)


def send(store, game, token=RED, kind="message", **fields):
    current = store.load(game["id"])
    return store.apply(
        game["id"],
        token,
        {"kind": kind, "command_id": uuid.uuid4().hex, "expected_version": current["version"], **fields},
    )


def run(coro):
    return asyncio.run(coro)


def test_provider_result_commits_once_and_gets_only_own_observation(tmp_path):
    async def scenario():
        provider = FakeProvider()
        store, game, runtime = setup(tmp_path, provider)
        other, _ = send(store, game, BLUE, text="private BLUE words")
        state, actor = send(store, game, text="private RED words")
        runtime.schedule(state, actor)
        runtime.schedule(state, actor)
        await runtime.drain()
        assert provider.calls == 1
        request = provider.requests[0]
        assert "private BLUE words" not in json.dumps(request)
        assert RED not in json.dumps(request)
        assert "scores" not in request and "conversations" not in request
        saved = store.load(game["id"])
        chat = saved["conversations"][actor]
        assert chat["work"]["status"] == "succeeded" and chat["join_opponent"] is True
        assert len(chat["messages"]) == 3
        assert chat["messages"][-1]["content"] == "A bounded reply."
        assert store.finish_job(chat["work"]["request_id"], "failed", "late") is None
        assert store.load(game["id"])["version"] == saved["version"]
        assert view(saved, "player_blue")["conversations"][actor]["work"] is None
        report = store.runtime_report(game["id"], actor)
        assert report["identity"] == provider.identity.model_dump()
        assert report["attempts"][0]["charged_tokens"] == 7
        assert report["attempts"][0]["charged_cost"] == 2
        assert report["attempts"][0]["latency_ms"] >= 0
        await runtime.close()

    run(scenario())


@pytest.mark.parametrize(
    "behavior,code",
    [
        ("invalid", "invalid_response"),
        ("blank", "invalid_response"),
        ("error", "provider_error"),
        ("bad_usage", "usage_exceeded"),
    ],
)
def test_invalid_outputs_do_not_mutate_dialogue_or_recruit(tmp_path, behavior, code):
    async def scenario():
        provider = FakeProvider(behavior)
        store, game, runtime = setup(tmp_path, provider)
        state, actor = send(store, game, text="hello")
        runtime.schedule(state, actor)
        await runtime.drain()
        saved = store.load(game["id"])
        chat = saved["conversations"][actor]
        assert chat["work"]["status"] == "failed"
        assert chat["work"]["error"] == code
        assert len(chat["messages"]) == 2
        assert not chat["join_opponent"]
        assert "DO_NOT_EXPOSE" not in json.dumps(saved)
        attempt = store.runtime_report(game["id"], actor)["attempts"][0]
        assert attempt["charged_tokens"] >= 20
        assert attempt["charged_cost"] >= 5
        assert provider.calls == 1  # No automatic retries for malformed output or arbitrary errors.
        send(store, game, kind="done")  # A failed provider cannot trap the player in conversation.
        await runtime.close()

    run(scenario())


def test_transient_failure_retries_with_separate_budget_charges(tmp_path):
    async def scenario():
        provider = FakeProvider("transient")
        store, game, runtime = setup(tmp_path, provider)
        state, actor = send(store, game, text="hello")
        runtime.schedule(state, actor)
        await runtime.drain()
        assert provider.calls == 2
        rows = store.runtime_report(game["id"], actor)["attempts"]
        assert [r["status"] for r in rows] == ["transient_error", "succeeded"]
        assert sum(r["charged_cost"] for r in rows) == 7
        assert store.load(game["id"])["conversations"][actor]["work"]["status"] == "succeeded"
        await runtime.close()

    run(scenario())


@pytest.mark.parametrize("limit", [{"call_limit": 1}, {"token_limit": 20}, {"cost_limit_microusd": 5}])
def test_retry_cannot_bypass_game_budget(tmp_path, limit):
    async def scenario():
        provider = FakeProvider("always_transient")
        policy = config(**({"cost_limit_microusd": 100} | limit))
        store, game, runtime = setup(tmp_path, provider, policy)
        state, actor = send(store, game, text="hello")
        runtime.schedule(state, actor)
        await runtime.drain()
        assert provider.calls == 1
        assert store.load(game["id"])["conversations"][actor]["work"]["error"] == "budget_exhausted"
        state, actor = send(store, game, kind="retry")
        runtime.schedule(state, actor)
        await runtime.drain()
        assert provider.calls == 1
        assert len(store.load(game["id"])["conversations"][actor]["messages"]) == 2
        await runtime.close()

    run(scenario())


def test_zero_spend_default_blocks_costed_provider_before_call(tmp_path):
    async def scenario():
        provider = FakeProvider()
        store, game, runtime = setup(tmp_path, provider, config())
        state, actor = send(store, game, text="hello")
        runtime.schedule(state, actor)
        await runtime.drain()
        assert provider.calls == 0
        assert store.load(game["id"])["conversations"][actor]["work"]["error"] == "budget_exhausted"
        await runtime.close()

    run(scenario())


def test_timeout_discards_late_result_and_retains_reservation(tmp_path):
    async def scenario():
        provider = FakeProvider("late", delay=0.2)
        store, game, runtime = setup(
            tmp_path, provider, config(timeout_seconds=0.01, cost_limit_microusd=100)
        )
        state, actor = send(store, game, text="hello")
        runtime.schedule(state, actor)
        await runtime.drain()
        timed_out = store.load(game["id"])
        assert timed_out["conversations"][actor]["work"]["error"] == "timeout"
        await asyncio.sleep(0.04)
        assert store.load(game["id"]) == timed_out
        assert store.runtime_report(game["id"], actor)["attempts"][0]["charged_cost"] == 5
        await runtime.close()

    run(scenario())


def test_cancel_during_call_then_retry_accepts_only_new_request(tmp_path):
    async def scenario():
        provider = FakeProvider("late", delay=0.1)
        store, game, runtime = setup(tmp_path, provider)
        state, actor = send(store, game, text="hello")
        old_id = state["conversations"][actor]["work"]["request_id"]
        runtime.schedule(state, actor)
        await asyncio.sleep(0.01)
        send(store, game, kind="cancel")
        runtime.cancel(old_id)
        await runtime.drain()
        state, actor = send(store, game, kind="retry")
        new_id = state["conversations"][actor]["work"]["request_id"]
        assert new_id != old_id
        runtime.schedule(state, actor)
        await runtime.drain()
        saved = store.load(game["id"])
        assert len(saved["conversations"][actor]["messages"]) == 3
        assert saved["conversations"][actor]["work"]["request_id"] == new_id
        rows = store.runtime_report(game["id"], actor)["attempts"]
        assert [r["status"] for r in rows] == ["cancelled", "succeeded"]
        assert rows[0]["charged_cost"] == 5
        await runtime.close()

    run(scenario())


def test_concurrency_and_shared_game_budget(tmp_path):
    async def scenario():
        provider = FakeProvider(delay=0.02)
        store, game, runtime = setup(
            tmp_path, provider, config(concurrency=1, call_limit=1, cost_limit_microusd=100)
        )
        for token in [RED, BLUE]:
            state, actor = send(store, game, token, text="hello")
            runtime.schedule(state, actor)
        await runtime.drain()
        assert provider.peak == 1 and provider.calls == 1
        states = [c["work"]["status"] for c in store.load(game["id"])["conversations"].values()]
        assert sorted(states) == ["failed", "succeeded"]
        await runtime.close()

    run(scenario())


def test_restart_interrupts_work_without_reissuing_or_refunding(tmp_path):
    provider = FakeProvider()
    store, game, _ = setup(tmp_path, provider)
    state, actor = send(store, game, text="hello")
    request_id = state["conversations"][actor]["work"]["request_id"]
    assert store.reserve_attempt(request_id) == 1
    with TestClient(create_app(store.path, provider=provider)) as client:
        restored = client.get(f"/api/games/{game['id']}", headers={"Authorization": "Bearer " + RED}).json()
        assert restored["conversations"][actor]["work"]["status"] == "interrupted"
        assert provider.calls == 0
        report = client.get(
            f"/api/games/{game['id']}/runtime", headers={"Authorization": "Bearer " + RED}
        ).json()
        assert report["attempts"][0]["status"] == "interrupted"
        assert report["attempts"][0]["charged_cost"] == 5
        assert client.get(f"/api/games/{game['id']}/runtime").status_code == 401
        other = client.get(
            f"/api/games/{game['id']}/runtime", headers={"Authorization": "Bearer " + BLUE}
        ).json()
        assert other["attempts"] == []


def test_provider_change_does_not_silently_resume_game(tmp_path):
    async def scenario():
        provider = FakeProvider()
        store, game, runtime = setup(tmp_path, provider)
        state, actor = send(store, game, text="hello")
        runtime.provider = ScriptedProvider()
        runtime.schedule(state, actor)
        await runtime.drain()
        assert store.load(game["id"])["conversations"][actor]["work"]["error"] == "provider_changed"
        assert provider.calls == 0

    run(scenario())


def test_v1_snapshot_and_replay_upgrade_without_fake_provider_events(tmp_path):
    store, game, _ = setup(tmp_path, ScriptedProvider())
    legacy = deepcopy(game)
    legacy["schema_version"] = "1"
    for seat, chat in legacy["conversations"].items():
        chat.pop("work")
        chat.pop("join_opponent")
        chat["messages"] += [{"name": seat, "content": "old one"}, {"name": seat, "content": "old two"}]
    with store.connection() as db:
        db.execute("UPDATE games SET state=? WHERE id=?", (json.dumps(legacy), game["id"]))
        db.execute(
            "UPDATE events SET state=? WHERE game_id=? AND version=?",
            (json.dumps(legacy), game["id"], game["version"]),
        )
    restored = store.load(game["id"])
    assert restored["schema_version"] == "2"
    assert restored["version"] == legacy["version"]
    assert restored["conversations"]["player_red"]["join_opponent"]
    assert restored["conversations"]["player_red"]["work"] is None
    assert store.replay(game["id"], "player_red")[-1] == view(restored, "player_red")
    assert store.runtime_report(game["id"], "player_red")["attempts"] == []


def test_queue_capacity_and_cancel_before_provider_start(tmp_path):
    async def scenario():
        provider = FakeProvider(delay=0.2)
        store, game, runtime = setup(tmp_path, provider, config(max_queued=1, cost_limit_microusd=100))
        state, actor = send(store, game, text="hello")
        runtime.schedule(state, actor)
        other, blue_actor = send(store, game, BLUE, text="hello")
        runtime.schedule(other, blue_actor)
        assert store.load(game["id"])["conversations"][blue_actor]["work"]["error"] == "capacity"
        request_id = state["conversations"][actor]["work"]["request_id"]
        send(store, game, kind="cancel")
        runtime.cancel(request_id)
        await runtime.drain()
        assert provider.calls == 0
        assert store.load(game["id"])["conversations"][actor]["work"]["status"] == "cancelled"
        assert store.runtime_report(game["id"], actor)["attempts"] == []
        await runtime.close()

    run(scenario())


def test_declared_usage_violation_blocks_subsequent_calls(tmp_path):
    async def scenario():
        provider = FakeProvider("bad_usage")
        store, game, runtime = setup(tmp_path, provider)
        state, actor = send(store, game, text="hello")
        runtime.schedule(state, actor)
        await runtime.drain()
        state, actor = send(store, game, kind="retry")
        runtime.schedule(state, actor)
        await runtime.drain()
        assert provider.calls == 1
        assert store.load(game["id"])["conversations"][actor]["work"]["error"] == "provider_bounds_exceeded"
        assert store.runtime_report(game["id"], actor)["attempts"][0]["charged_tokens"] == 1004
        await runtime.close()

    run(scenario())


def test_pending_reply_blocks_message_and_round_completion(tmp_path):
    from game.core import GameError

    store, game, _ = setup(tmp_path, FakeProvider())
    send(store, game, text="hello")
    for kind, fields in [("message", {"text": "too soon"}), ("done", {})]:
        with pytest.raises(GameError, match="reply or cancel"):
            send(store, game, kind=kind, **fields)
    send(store, game, kind="cancel")
    send(store, game, kind="done")


def test_late_completion_after_round_change_is_discarded(tmp_path):
    store, game, _ = setup(tmp_path, FakeProvider())
    state, actor = send(store, game, text="hello")
    request_id = state["conversations"][actor]["work"]["request_id"]
    send(store, game, kind="cancel")
    send(store, game, kind="done")
    send(store, game, BLUE, kind="done")
    state, _ = send(store, game, kind="advance")
    assert (
        store.finish_job(
            request_id,
            "succeeded",
            result={
                "decision": {"dialogue": "Too late", "join_opponent": True},
                "usage": {"input_tokens": 0, "output_tokens": 0, "cost_microusd": 0},
            },
        )
        is None
    )
    assert store.load(game["id"]) == state


def test_replayed_cancel_does_not_cancel_new_work_or_fail_in_next_round(tmp_path):
    provider = FakeProvider(delay=0.1)
    store, game, _ = setup(tmp_path, provider)
    app = create_app(store.path, provider=provider, policy=config(cost_limit_microusd=100))
    with TestClient(app) as client:
        url = f"/api/games/{game['id']}/commands"
        headers = {"Authorization": f"Bearer {RED}"}

        def command(kind, **fields):
            body = {
                "kind": kind,
                "command_id": uuid.uuid4().hex,
                "expected_version": store.load(game["id"])["version"],
                **fields,
            }
            response = client.post(url, headers=headers, json=body)
            assert response.status_code == 200, response.text
            return body, response.json()

        command("message", text="hello")
        old_cancel, _ = command("cancel")
        _, retried = command("retry")
        response = client.post(url, headers=headers, json=old_cancel)
        assert response.status_code == 200
        assert (
            response.json()["conversations"]["player_red"]["work"]
            == retried["conversations"]["player_red"]["work"]
        )
        client.portal.call(app.state.runtime.drain)
        assert store.load(game["id"])["conversations"]["player_red"]["work"]["status"] == "succeeded"
        command("done")
        send(store, game, BLUE, kind="done")
        command("advance")
        response = client.post(url, headers=headers, json=old_cancel)
        assert response.status_code == 200
        assert response.json()["conversations"]["player_red"]["work"] is None
