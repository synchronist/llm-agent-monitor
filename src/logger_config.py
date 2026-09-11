import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import ROOT


def configure_logging(log_path: Path = ROOT / "logs" / "app.log") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("llm_agent_monitor")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    file = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(console)
    logger.addHandler(file)
