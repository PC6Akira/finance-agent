"""引擎 / 会话 / 建表。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base
from src.config import settings

engine = create_engine(f"sqlite:///{settings.db_path}")
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """建表（幂等）。"""
    Base.metadata.create_all(engine)
