import pytest
import requests


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    for name in ("LLM_PROVIDER", "OPENAI_API_KEY", "OPENAI_MODEL", "MAX_RETRIES", "REQUEST_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("src.config.load_dotenv", lambda *args, **kwargs: None)

    def block_network(*args, **kwargs):
        raise AssertionError("Real HTTP is forbidden in tests")

    monkeypatch.setattr(requests.sessions.Session, "request", block_network)
