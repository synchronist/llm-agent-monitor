from unittest.mock import Mock

import pytest
import requests

from src.config import Settings
from src.llm_client import LLMError, OpenAILLMClient


def response(status=200, payload=None):
    return Mock(status_code=status, json=Mock(return_value=payload if payload is not None else {
        "status": "completed", "output": [
            {"type": "reasoning"},
            {"type": "message", "content": [{"type": "output_text", "text": "Olá"}]},
        ],
    }))


@pytest.fixture
def client():
    return OpenAILLMClient(Settings("openai", "test-key", "test-model", 2, 5))


def test_http_contract(client, monkeypatch):
    post = Mock(return_value=response())
    monkeypatch.setattr(requests, "post", post)
    assert client.generate("Teste") == "Olá"
    assert post.call_args.args == ("https://api.openai.com/v1/responses",)
    assert post.call_args.kwargs["timeout"] == 5
    assert post.call_args.kwargs["json"] == {"model": "test-model", "input": "Teste", "store": False}
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


@pytest.mark.parametrize("failure", [response(429), response(500), response(408), response(409), requests.Timeout(), requests.ConnectionError()])
def test_retry_then_success(client, monkeypatch, failure):
    post = Mock(side_effect=[failure, response()])
    sleep = Mock()
    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr("src.llm_client.time.sleep", sleep)
    assert client.generate("Teste") == "Olá"
    assert post.call_count == 2
    sleep.assert_called_once_with(1)


def test_retries_exhausted(client, monkeypatch):
    post, sleep = Mock(return_value=response(503)), Mock()
    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr("src.llm_client.time.sleep", sleep)
    with pytest.raises(LLMError, match="esgotadas"):
        client.generate("Teste")
    assert post.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2]


@pytest.mark.parametrize("status", [400, 401, 403, 404, 302])
def test_no_retry_on_permanent_error(client, monkeypatch, status):
    post = Mock(return_value=response(status))
    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(LLMError, match=str(status)):
        client.generate("Teste")
    assert post.call_count == 1


@pytest.mark.parametrize("payload", [[], {}, {"status": "incomplete"}, {"status": "completed", "output": []}, {"status": "completed", "output": None}])
def test_malformed_or_empty_response(client, monkeypatch, payload):
    monkeypatch.setattr(requests, "post", Mock(return_value=response(payload=payload)))
    with pytest.raises(LLMError):
        client.generate("Teste")


def test_invalid_json(client, monkeypatch):
    bad = response()
    bad.json.side_effect = ValueError("secret raw body")
    monkeypatch.setattr(requests, "post", Mock(return_value=bad))
    with pytest.raises(LLMError, match="JSON inválida") as error:
        client.generate("Teste")
    assert "secret" not in str(error.value)
