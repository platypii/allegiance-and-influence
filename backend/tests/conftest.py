import pytest


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch):
    """Verification never inherits a user's live model configuration or credential."""
    monkeypatch.delenv("GAME_MODEL_CONFIG", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY_FILE", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
