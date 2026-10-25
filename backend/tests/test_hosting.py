"""Hosted entry points must fail before opening a disposable production database."""

import os
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient
from game.app import create_app
from game.store import Store

ROOT = Path(__file__).resolve().parents[2]


def test_publish_requires_durable_database():
    env = {key: value for key, value in os.environ.items() if key != "DATABASE_URL"}
    result = subprocess.run(
        ["bash", "scripts/replit-start.sh"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 1
    assert "Publishing requires DATABASE_URL" in result.stderr


def test_explicit_path_never_connects_to_environment_database(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unreachable.invalid/do-not-connect")
    with TestClient(create_app(tmp_path / "local.db")) as client:
        assert type(client.app.state.store) is Store
        assert client.get("/api/health").status_code == 200
