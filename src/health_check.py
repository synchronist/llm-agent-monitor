import json
import os
import time

from src.config import load_settings
from src.llm_client import LLMError, create_client
from src.logger_config import configure_logging
from src.models import utc_timestamp


def main() -> int:
    started = time.perf_counter()
    result: dict[str, str | float] = {}
    try:
        configure_logging()
        settings = load_settings()
        result["provider"] = settings.provider
        create_client(settings).generate("Responda apenas OK.")
        result["status"] = "healthy"
    except (ValueError, OSError, LLMError) as exc:
        result.update(provider=os.getenv("LLM_PROVIDER", "mock").strip().lower(),
                      status="unavailable", error=str(exc))
    result.update(latency_ms=round((time.perf_counter() - started) * 1000, 3),
                  timestamp=utc_timestamp())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
