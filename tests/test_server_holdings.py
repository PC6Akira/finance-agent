"""FastAPI 持仓 + 推荐问题接口测试（monkeypatch 掉 akshare 基金名查询）。"""
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from db.database import SessionLocal
from db.models import Message, User, UserHolding
from server.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def authed(client, monkeypatch):
    # 让 add_holding 的基金名查询不触网
    monkeypatch.setattr("src.user._fund_name", lambda code: "测试基金")
    name = "test_" + secrets.token_hex(4)
    client.post("/api/auth/register", json={"username": name, "password": "pw123"})
    token = client.post("/api/auth/login", json={"username": name, "password": "pw123"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    yield name, headers
    with SessionLocal() as s:  # 清理用户 + 持仓 + 对话
        s.execute(delete(UserHolding).where(UserHolding.username == name))
        s.execute(delete(Message).where(Message.username == name))
        s.execute(delete(User).where(User.username == name))
        s.commit()


def test_holdings_require_auth(client):
    assert client.get("/api/holdings").status_code == 401
    assert client.get("/api/recommend").status_code == 401


def test_add_list_remove(client, authed):
    name, headers = authed

    # 空列表
    r = client.get("/api/holdings", headers=headers)
    assert r.status_code == 200 and r.json() == []

    # 添加（金额非法被拒）
    r = client.post("/api/holdings", json={"fund_code": "110022", "amount": 0}, headers=headers)
    assert r.status_code == 400

    # 正常添加
    r = client.post("/api/holdings", json={"fund_code": "110022", "amount": 1000, "cost": 1.5}, headers=headers)
    assert r.status_code == 200

    r = client.get("/api/holdings", headers=headers)
    assert r.status_code == 200
    assert r.json()[0]["fund_code"] == "110022"
    assert r.json()[0]["fund_name"] == "测试基金"

    # 推荐问题（有持仓 → 3 条）
    r = client.get("/api/recommend", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 3

    # 删除
    r = client.delete("/api/holdings/110022", headers=headers)
    assert r.status_code == 200
    assert client.get("/api/holdings", headers=headers).json() == []
