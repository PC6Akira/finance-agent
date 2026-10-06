"""FastAPI 后端入口：挂载 API 路由 + 静态前端。

运行：
    .venv/bin/python -m uvicorn server.main:app --reload
或：
    .venv/bin/python server/main.py
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db.database import init_db
from server.auth_api import router as auth_router
from server.chat_api import router as chat_router
from server.fund_api import router as fund_router
from server.holding_api import router as holding_router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="基金投研 Agent 后端", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(holding_router)
app.include_router(fund_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# 静态前端（同源挂载，免 CORS；须在所有 API 路由之后）
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    from src.config import settings

    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
