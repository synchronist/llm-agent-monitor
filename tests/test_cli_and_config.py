import json
from unittest.mock import Mock

import pytest

import main
from src.config import Settings, load_settings
from src.health_check import main as health_main
from src.llm_client import LLMError


@pytest.mark.parametrize("kwargs", [{"provider": "other"}, {"provider": "openai"}, {"max_retries": -1}, {"max_retries": 11}, {"timeout": 0}, {"timeout": float("nan")}, {"timeout": float("inf")}])
def test_invalid_settings(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)


def test_default_mock_and_invalid_number(monkeypatch):
    assert load_settings().provider == "mock"
    monkeypatch.setenv("MAX_RETRIES", "abc")
    with pytest.raises(ValueError, match="inteiro"):
        load_settings()


def test_cli_output_and_continue_after_failure(tmp_path, monkeypatch):
    source, output = tmp_path / "in.json", tmp_path / "out.json"
    source.write_text('[{"id":"a","prompt":"hi"},{"id":"b","prompt":"hello"}]')
    monkeypatch.setattr(main, "configure_logging", lambda: None)
    assert main.main(["--input", str(source), "--output", str(output)]) == 0
    assert len(json.loads(output.read_text())) == 2
    client = Mock(provider="mock")
    client.generate.side_effect = [LLMError("failure"), "ok"]
    monkeypatch.setattr(main, "create_client", lambda settings: client)
    assert main.main(["--input", str(source), "--output", str(output)]) == 1
    assert [r["status"] for r in json.loads(output.read_text())] == ["error", "success"]
    assert main.main(["--input", str(source), "--output", str(source)]) == 1
    assert json.loads(source.read_text())[0]["id"] == "a"


def test_health_check(capsys, monkeypatch):
    monkeypatch.setattr("src.health_check.configure_logging", lambda: None)
    assert health_main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "healthy"
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    assert health_main() == 1
    assert json.loads(capsys.readouterr().out)["status"] == "unavailable"
