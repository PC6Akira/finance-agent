"""静态前端挂载测试。"""
from fastapi.testclient import TestClient

from server.main import app


def test_static_serving():
    with TestClient(app) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "基金投研 Agent" in r.text

        r = c.get("/app.js")
        assert r.status_code == 200
        assert "javascript" in r.headers["content-type"]

        r = c.get("/vendor/echarts.min.js")
        assert r.status_code == 200

        # 健康检查不能被静态 catch-all 截胡
        assert c.get("/api/health").json() == {"status": "ok"}
