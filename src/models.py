from dataclasses import dataclass
from datetime import datetime, timezone


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Task:
    id: str
    prompt: str


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    provider: str
    status: str
    latency_ms: float
    response: str | None
    timestamp: str
    error: str | None = None
