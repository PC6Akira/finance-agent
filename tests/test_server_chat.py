"""FastAPI 对话接口测试（monkeypatch 掉真实 goal loop，不发真 LLM 请求）。"""
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from db.database import SessionLocal
from db.models import Message, User
from server.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def authed(client):
    name = "test_" + secrets.token_hex(4)
    client.post("/api/auth/register", json={"username": name, "password": "pw123"})
    token = client.post("/api/auth/login", json={"username": name, "password": "pw123"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    yield name, headers
    with SessionLocal() as s:  # 清理用户 + 对话
        s.execute(delete(Message).where(Message.username == name))
        s.execute(delete(User).where(User.username == name))
        s.commit()


def test_chat_requires_auth(client):
    r = client.post("/api/chat", json={"message": "你好"})
    assert r.status_code == 401


def test_chat_empty_message(client, authed):
    _, headers = authed
    r = client.post("/api/chat", json={"message": "   "}, headers=headers)
    assert r.status_code == 400


def test_chat_flow(client, authed, monkeypatch):
    name, headers = authed

    def fake_run(goal, history=None, ask_user=None, **kwargs):
        return f"已收到：{goal}"

    monkeypatch.setattr("server.chat_api.run", fake_run)

    r = client.post("/api/chat", json={"message": "分析 110022"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["reply"] == "已收到：分析 110022"

    from src import user
    roles = [role for role, _ in user.recent_messages(name, limit=10)]
    assert roles == ["user", "assistant"]
