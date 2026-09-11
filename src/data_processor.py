import json
import re
from dataclasses import asdict
from pathlib import Path

from src.models import Task, TaskResult


def load_tasks(path: Path) -> list[Task]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Não foi possível ler JSON em {path}: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ValueError("A entrada deve ser uma lista não vazia de tarefas.")
    tasks = []
    seen = set()
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Tarefa {index}: esperado um objeto JSON.")
        for key in ("id", "prompt"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"Tarefa {index}: {key} deve ser texto não vazio.")
        task_id = item["id"].strip()
        if not re.fullmatch(r"[\w.-]+", task_id):
            raise ValueError(f"Tarefa {index}: id deve conter letras, números, _, . ou -.")
        if task_id in seen:
            raise ValueError(f"Tarefa {index}: ID duplicado: {task_id}.")
        seen.add(task_id)
        # Preserve line breaks and indentation for prompts containing code.
        prompt = item["prompt"].replace("\r\n", "\n").replace("\r", "\n")
        prompt = "\n".join(line.rstrip() for line in prompt.split("\n")).strip()
        tasks.append(Task(task_id, prompt))
    return tasks


def save_results(path: Path, results: list[TaskResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
