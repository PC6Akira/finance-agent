"""FastAPI 基金数据 / 数据源接口测试（monkeypatch 掉 akshare 数据源）。"""
import secrets

import pandas as pd
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
    with SessionLocal() as s:
        s.execute(delete(Message).where(Message.username == name))
        s.execute(delete(User).where(User.username == name))
        s.commit()


def _fake_nav():
    return pd.DataFrame({
        "净值日期": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "单位净值": [1.0, 1.1, 1.2],
        "日增长率": [0.0, 10.0, 9.0],
    })


def _fake_holdings():
    return pd.DataFrame({
        "季度": ["2024Q1", "2024Q1"],
        "股票代码": ["600000", "000001"],
        "股票名称": ["浦发银行", "平安银行"],
        "占净值比例": [5.0, 4.0],
    })


def _fake_industry():
    return pd.DataFrame({
        "截止时间": ["2024-03-31", "2024-06-30"],
        "行业类别": ["制造业", "金融业"],
        "占净值比例": [20.0, 30.0],
    })


def test_fund_requires_auth(client):
    assert client.get("/api/fund/110022").status_code == 401


def test_fund_detail(client, authed, monkeypatch):
    _, headers = authed
    monkeypatch.setattr("data_sources.fund.get_fund_nav", lambda code: _fake_nav())
    monkeypatch.setattr("data_sources.fund.get_fund_holdings", lambda code, year: _fake_holdings())
    monkeypatch.setattr("data_sources.fund.get_fund_industry_allocation", lambda code, year: _fake_industry())

    r = client.get("/api/fund/110022", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert data["fund_code"] == "110022"
    assert data["nav"]["dates"] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert data["nav"]["nav"] == [1.0, 1.1, 1.2]
    assert data["holdings"][0]["stock_name"] == "浦发银行"
    assert data["industry"]["labels"] == ["金融业"]
    assert data["backtest"]["dates"] == data["nav"]["dates"]
    assert isinstance(data["risk_points"], list)


def test_datasource_reports(client, authed, monkeypatch):
    _, headers = authed
    monkeypatch.setattr("data_sources.fund.get_fund_reports",
                        lambda code: pd.DataFrame({"基金名称": ["测试基金"], "报告期": ["2024Q1"]}))

    r = client.get("/api/datasource/reports/110022", headers=headers)
    assert r.status_code == 200
    assert r.json()[0]["基金名称"] == "测试基金"
