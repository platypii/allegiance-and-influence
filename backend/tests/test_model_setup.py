import json
import os
import runpy
import stat
import subprocess
from pathlib import Path

import pytest
from game.credentials import openrouter_key
from game.model_config import configured_provider

ROOT = Path(__file__).resolve().parents[2]
SETUP = runpy.run_path(str(ROOT / "scripts/model_setup.py"))
ROSTER = json.loads((ROOT / "gameplay/characters.json").read_text())


def test_private_key_creation_and_explicit_file_loading(tmp_path, monkeypatch):
    path = tmp_path / "openrouter.key"
    SETUP["save_key"](path, "fixture-private-key")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    monkeypatch.setenv("OPENROUTER_API_KEY", "different-environment-key")
    monkeypatch.setenv("OPENROUTER_API_KEY_FILE", str(path))
    assert openrouter_key() == "fixture-private-key"
    assert openrouter_key(path) == "fixture-private-key"
    monkeypatch.delenv("OPENROUTER_API_KEY_FILE")
    assert openrouter_key() == "different-environment-key"
    with pytest.raises(FileExistsError):
        SETUP["save_key"](path, "replacement")
    assert path.read_text().strip() == "fixture-private-key"


def test_key_creation_rejects_symlinks_and_bad_values(tmp_path):
    existing = tmp_path / "existing.key"
    existing.write_text("existing-value")
    link = tmp_path / "link.key"
    link.symlink_to(existing)
    with pytest.raises(FileExistsError):
        SETUP["save_key"](link, "replacement")
    assert existing.read_text() == "existing-value"
    for value in ["", "two tokens", "x" * 4097]:
        with pytest.raises(ValueError):
            SETUP["save_key"](tmp_path / "new.key", value)
    assert not (tmp_path / "new.key").exists()


def test_key_errors_do_not_expose_file_contents(tmp_path):
    path = tmp_path / "bad.key"
    path.write_text("private-secret with-invalid-space")
    with pytest.raises(ValueError) as caught:
        openrouter_key(path)
    assert "private-secret" not in str(caught.value)
    with pytest.raises(ValueError, match="Cannot read"):
        openrouter_key(tmp_path / "missing")


def test_configured_router_uses_file_but_does_not_persist_key(tmp_path, monkeypatch):
    path = tmp_path / "models.json"
    path.write_text((ROOT / "config/models.example.json").read_text())
    key = tmp_path / "key"
    SETUP["save_key"](key, "fixture-secret")
    monkeypatch.setenv("GAME_MODEL_CONFIG", str(path))
    monkeypatch.setenv("OPENROUTER_API_KEY_FILE", str(key))
    provider, _ = configured_provider(ROSTER)
    assert provider.for_character("albert_einstein")._api_key == "fixture-secret"
    assert "fixture-secret" not in provider.config.model_dump_json()
    assert "fixture-secret" not in json.dumps(SETUP["inspect_config"](path))


def test_setup_commands_do_not_overwrite_or_accept_piped_keys(tmp_path):
    script = ROOT / "scripts/model_setup.py"
    python = ROOT / ".venv/bin/python"
    path = tmp_path / "models.json"
    result = subprocess.run([python, script, "init", "--config", path], capture_output=True, text=True)
    assert result.returncode == 0
    original = path.read_bytes()
    repeated = subprocess.run([python, script, "init", "--config", path], capture_output=True, text=True)
    assert repeated.returncode == 2 and path.read_bytes() == original
    key_path = tmp_path / "key"
    piped = subprocess.run(
        [python, script, "key", "--file", key_path], input="piped-secret\n", capture_output=True, text=True
    )
    assert piped.returncode == 2 and not key_path.exists()
    assert "piped-secret" not in piped.stdout + piped.stderr
    inspected = subprocess.run([python, script, "check", "--config", path], capture_output=True, text=True)
    assert inspected.returncode == 0
    assert json.loads(inspected.stdout)["characters"]["albert_einstein"] == "model_a"


def test_setup_budget_inspection_uses_profile_cost(tmp_path):
    config = json.loads((ROOT / "config/models.example.json").read_text())
    config["profiles"]["model_a"]["max_prompt_usd_per_million"] = 1.0
    path = tmp_path / "models.json"
    path.write_text(json.dumps(config))
    report = SETUP["inspect_config"](path)
    assert report["profiles"]["model_a"]["fits_game_budget"] is False
    assert report["profiles"]["control"]["reservation_usd"] == "0"


def test_launcher_rejects_missing_config_before_starting():
    result = subprocess.run(
        ["bash", "scripts/run-local.sh", "--models"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "GAME_PORT": "1"},
    )
    assert result.returncode == 2 and "Missing value" in result.stderr
