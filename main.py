import argparse
import logging
from pathlib import Path

from src.agent import Agent
from src.config import ROOT, load_settings
from src.data_processor import load_tasks, save_results
from src.llm_client import create_client
from src.logger_config import configure_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute e monitore tarefas de LLM em JSON.")
    parser.add_argument("--input", type=Path, default=ROOT / "data/input.example.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/output.json")
    args = parser.parse_args(argv)
    try:
        configure_logging()
        logging.getLogger("llm_agent_monitor").info("Execution started")
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Entrada e saída devem ser arquivos diferentes.")
        settings = load_settings()
        tasks = load_tasks(args.input)
        agent = Agent(create_client(settings))
        results = [agent.run(task) for task in tasks]
        save_results(args.output, results)
        logging.getLogger("llm_agent_monitor").info("Saved %s results to %s", len(results), args.output)
        return 1 if any(result.status == "error" for result in results) else 0
    except (ValueError, OSError) as exc:
        logging.getLogger("llm_agent_monitor").error("Execution failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
