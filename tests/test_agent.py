from datetime import datetime
from unittest.mock import Mock

from src.agent import Agent
from src.llm_client import LLMError, MockLLMClient
from src.models import Task


def test_mock_agent():
    result = Agent(MockLLMClient()).run(Task("a", "Olá"))
    assert result.status == "success"
    assert result.response == "[MOCK] Resposta simulada para: Olá"
    assert result.provider == "mock"
    assert result.latency_ms >= 0
    assert datetime.fromisoformat(result.timestamp).tzinfo is not None


def test_error_result():
    client = Mock(provider="openai")
    client.generate.side_effect = LLMError("OpenAI: HTTP 401.")
    result = Agent(client).run(Task("a", "Olá"))
    assert result.status == "error"
    assert result.response is None
    assert result.error == "OpenAI: HTTP 401."
