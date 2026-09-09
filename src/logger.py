"""日志：写到 logs/app.log，任务 / 工具调用 / 错误可追溯。"""
import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:  # 避免重复添加 handler
        LOG_DIR.mkdir(exist_ok=True)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        fh = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
    return logger
