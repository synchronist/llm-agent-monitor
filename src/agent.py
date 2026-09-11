import logging
import time

from src.llm_client import LLMClient, LLMError
from src.models import Task, TaskResult, utc_timestamp

logger = logging.getLogger("llm_agent_monitor")


class Agent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def run(self, task: Task) -> TaskResult:
        logger.info("Task %s started | Provider: %s", task.id, self.client.provider)
        started = time.perf_counter()
        response, error = None, None
        try:
            response = self.client.generate(task.prompt)
            status = "success"
        except LLMError as exc:
            status, error = "error", str(exc)
        latency = round((time.perf_counter() - started) * 1000, 3)
        logger.log(logging.INFO if status == "success" else logging.ERROR,
                   "Task %s %s in %sms%s", task.id, status, latency,
                   f" | {error}" if error else "")
        return TaskResult(task.id, self.client.provider, status, latency,
                          response, utc_timestamp(), error)
