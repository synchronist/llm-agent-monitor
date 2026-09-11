import json

import pytest

from src.data_processor import load_tasks, save_results
from src.models import TaskResult


def write_input(tmp_path, data):
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_and_normalize(tmp_path):
    tasks = load_tasks(write_input(tmp_path, [{"id": " task-1 ", "prompt": " Olá  \r\n    código  \n"}]))
    assert tasks[0].id == "task-1"
    assert tasks[0].prompt == "Olá\n    código"


@pytest.mark.parametrize("data", [
    {}, [], [3], [{}], [{"id": "a", "prompt": "  "}],
    [{"id": "", "prompt": "hi"}], [{"id": 1, "prompt": "hi"}],
    [{"id": "a", "prompt": 3}], [{"id": "a\nb", "prompt": "hi"}],
])
def test_invalid_data(tmp_path, data):
    with pytest.raises(ValueError):
        load_tasks(write_input(tmp_path, data))


def test_duplicate_normalized_ids(tmp_path):
    with pytest.raises(ValueError, match="duplicado"):
        load_tasks(write_input(tmp_path, [{"id": "a", "prompt": "x"}, {"id": " a ", "prompt": "y"}]))


def test_invalid_json_and_missing_file(tmp_path):
    path = tmp_path / "bad.json"
    with pytest.raises(ValueError, match="ler JSON"):
        load_tasks(path)
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="ler JSON"):
        load_tasks(path)


def test_save_results(tmp_path):
    path = tmp_path / "nested" / "out.json"
    save_results(path, [TaskResult("a", "mock", "success", 1, "Olá", "2026-01-01T00:00:00+00:00")])
    assert json.loads(path.read_text(encoding="utf-8"))[0]["response"] == "Olá"
