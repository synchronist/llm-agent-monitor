import logging
import time
from typing import Protocol

import requests

from src.config import Settings

logger = logging.getLogger("llm_agent_monitor")


class LLMError(Exception):
    """A provider failure safe to include in logs and results."""


class LLMClient(Protocol):
    provider: str

    def generate(self, prompt: str) -> str: ...


class MockLLMClient:
    provider = "mock"

    def generate(self, prompt: str) -> str:
        return f"[MOCK] Resposta simulada para: {prompt}"


class OpenAILLMClient:
    provider = "openai"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, prompt: str) -> str:
        for attempt in range(self.settings.max_retries + 1):
            try:
                response = requests.post(
                    "https://api.openai.com/v1/responses",
                    headers={"Authorization": f"Bearer {self.settings.api_key}"},
                    json={"model": self.settings.model, "input": prompt, "store": False},
                    timeout=self.settings.timeout,
                    allow_redirects=False,
                )
            except (requests.Timeout, requests.ConnectionError):
                error = "OpenAI: timeout ou falha de conexão."
            except requests.RequestException:
                raise LLMError("OpenAI: falha ao enviar a requisição.") from None
            else:
                if response.status_code == 200:
                    return self._extract_text(response)
                error = f"OpenAI: HTTP {response.status_code}."
                if response.status_code not in {408, 409, 429} and not 500 <= response.status_code < 600:
                    raise LLMError(error + " Verifique credenciais, modelo e requisição.")
            if attempt == self.settings.max_retries:
                raise LLMError(error + " Tentativas esgotadas.")
            delay = min(2 ** attempt, 30)
            logger.warning("Provider openai retry %s/%s in %ss: %s",
                           attempt + 1, self.settings.max_retries, delay, error)
            time.sleep(delay)
        raise AssertionError("Unreachable retry state")

    @staticmethod
    def _extract_text(response: requests.Response) -> str:
        try:
            data = response.json()
            if data.get("status") != "completed":
                raise LLMError("OpenAI: resposta não concluída.")
            parts = [
                part["text"]
                for item in data["output"] if item.get("type") == "message"
                for part in item["content"] if part.get("type") == "output_text"
            ]
            text = "\n".join(parts).strip()
        except (ValueError, KeyError, TypeError, AttributeError):
            raise LLMError("OpenAI: resposta JSON inválida.") from None
        if not text:
            raise LLMError("OpenAI: resposta sem texto (possível recusa do modelo).")
        return text


def create_client(settings: Settings) -> LLMClient:
    if settings.provider == "mock":
        return MockLLMClient()
    return OpenAILLMClient(settings)
