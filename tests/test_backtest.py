"""回测策略单测（纯函数，合成净值）。"""
import pandas as pd

from src import backtest


def _nav(values):
    n = len(values)
    return pd.DataFrame({
        "净值日期": [f"2024-01-{i+1:02d}" for i in range(n)],
        "单位净值": values,
        "日增长率": [0.0] * n,
    })


def test_buy_hold():
    equity, invested = backtest.buy_hold(_nav([1.0, 1.1, 1.21]), {"initial_capital": 10000})
    assert invested == 10000
    assert abs(equity.iloc[-1] - 12100) < 0.01  # 10000 * 1.21


def test_dca():
    equity, invested = backtest.dca(_nav([1.0, 1.1, 1.21]), {"amount": 1000})
    assert invested == 1000  # 同一月份只投 1 次
    assert abs(equity.iloc[-1] - 1210) < 0.01


def test_compute_metrics():
    equity, invested = backtest.buy_hold(_nav([1.0, 1.1, 1.21]), {"initial_capital": 10000})
    m = backtest.compute_metrics(equity, invested)
    assert m["总收益率%"] == 21.0
    assert m["最大回撤%"] == 0.0
