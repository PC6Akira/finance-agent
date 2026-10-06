"""FastAPI 后端入口：挂载 API 路由 + 静态前端。

运行：
    .venv/bin/python -m uvicorn server.main:app --reload
或：
    .venv/bin/python server/main.py
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.database import init_db
from server.auth_api import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="基金投研 Agent 后端", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    from src.config import settings

    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
