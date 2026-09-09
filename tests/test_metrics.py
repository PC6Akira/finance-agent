"""指标函数单测（纯函数，无网络）。"""
import pandas as pd

from src import metrics


def _nav(values, daily=None):
    n = len(values)
    return pd.DataFrame({
        "净值日期": [f"2024-01-{i+1:02d}" for i in range(n)],
        "单位净值": values,
        "日增长率": daily if daily is not None else [0.0] * n,
    })


def test_period_return():
    assert abs(metrics.period_return(_nav([1.0, 1.1, 1.21])) - 21.0) < 0.01


def test_max_drawdown():
    assert abs(metrics.max_drawdown(_nav([1.0, 1.2, 0.9, 1.0])) - (-25.0)) < 0.01


def test_annualized_volatility_zero():
    assert metrics.annualized_volatility(_nav([1.0, 1.0])) == 0.0


def test_annualized_volatility_positive():
    nav = _nav([1.0, 1.01, 1.0], daily=[0.0, 1.0, -0.99])
    assert metrics.annualized_volatility(nav) > 0


def test_holdings_overlap():
    q = ["2026年1季度股票投资明细"]
    a = pd.DataFrame({"股票代码": ["600519", "000858", "000333"], "占净值比例": [9, 9, 8], "季度": q * 3})
    b = pd.DataFrame({"股票代码": ["600519", "000568", "600809"], "占净值比例": [9, 8, 7], "季度": q * 3})
    assert metrics.holdings_overlap(a, b) == ["600519"]
