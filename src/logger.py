"""日志：写到 logs/app.log，按体积轮转，总量约 50MB（新日志覆盖最旧的）。"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
MAX_BYTES = 5 * 1024 * 1024   # 单文件上限 5MB
BACKUP_COUNT = 9              # 保留 9 份历史备份 → 总量约 5MB × 10 = 50MB


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:  # 避免重复添加 handler
        LOG_DIR.mkdir(exist_ok=True)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        fh = RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
    return logger
