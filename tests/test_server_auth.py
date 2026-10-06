"""FastAPI 鉴权接口测试：注册 / 登录 / 当前用户 / 登出。"""
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from db.database import SessionLocal
from db.models import User
from server.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # 触发 lifespan（init_db）
        yield c


@pytest.fixture()
def username():
    name = "test_" + secrets.token_hex(4)
    yield name
    with SessionLocal() as s:  # 清理测试用户
        s.execute(delete(User).where(User.username == name))
        s.commit()


def test_auth_flow(client, username):
    # 注册成功
    r = client.post("/api/auth/register", json={"username": username, "password": "pw123"})
    assert r.status_code == 200

    # 重复注册被拒
    r = client.post("/api/auth/register", json={"username": username, "password": "pw123"})
    assert r.status_code == 400

    # 错误密码登录被拒
    r = client.post("/api/auth/login", json={"username": username, "password": "wrong"})
    assert r.status_code == 401

    # 正确登录，拿到 token
    r = client.post("/api/auth/login", json={"username": username, "password": "pw123"})
    assert r.status_code == 200
    token = r.json()["token"]
    assert token

    # 带 token 取当前用户
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == username

    # 不带 token 被拒
    assert client.get("/api/auth/me").status_code == 401

    # 登出
    r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

    # 登出后 token 失效
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
