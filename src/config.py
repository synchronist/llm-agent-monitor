import math
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    provider: str = "mock"
    api_key: str = field(default="", repr=False)
    model: str = ""
    max_retries: int = 3
    timeout: float = 30

    def __post_init__(self) -> None:
        if self.provider not in {"mock", "openai"}:
            raise ValueError("LLM_PROVIDER deve ser mock ou openai.")
        if not 0 <= self.max_retries <= 10:
            raise ValueError("MAX_RETRIES deve estar entre 0 e 10.")
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("REQUEST_TIMEOUT deve ser positivo e finito.")
        if self.provider == "openai" and (not self.api_key or not self.model):
            raise ValueError("Configure OPENAI_API_KEY e OPENAI_MODEL para usar openai.")


def load_settings(env_path: Path = ROOT / ".env") -> Settings:
    load_dotenv(env_path, override=False)
    try:
        retries = int(os.getenv("MAX_RETRIES", "3"))
        timeout = float(os.getenv("REQUEST_TIMEOUT", "30"))
    except ValueError:
        raise ValueError("MAX_RETRIES deve ser inteiro e REQUEST_TIMEOUT numérico.") from None
    return Settings(
        provider=os.getenv("LLM_PROVIDER", "mock").strip().lower(),
        api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        model=os.getenv("OPENAI_MODEL", "").strip(),
        max_retries=retries,
        timeout=timeout,
    )
