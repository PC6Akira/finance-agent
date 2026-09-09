"""诊断规则单测（纯函数，合成数据）。"""
import pandas as pd

from src import diagnosis


def _nav(values):
    n = len(values)
    return pd.DataFrame({
        "净值日期": [f"2024-01-{i+1:02d}" for i in range(n)],
        "单位净值": values,
        "日增长率": [0.0] * n,
    })


def _holdings(weights):
    n = len(weights)
    return pd.DataFrame({
        "股票代码": [f"{i:06d}" for i in range(n)],
        "股票名称": [f"股票{i}" for i in range(n)],
        "占净值比例": weights,
        "持股数": [100] * n,
        "持仓市值": [1000] * n,
        "季度": ["2026年1季度股票投资明细"] * n,
    })


def _industry():
    return pd.DataFrame({
        "行业类别": ["制造业", "金融业", "制造业"],
        "占净值比例": [86.0, 14.0, 85.0],
        "市值": [1000, 100, 990],
        "截止时间": ["2026-03-31", "2026-03-31", "2026-06-30"],
    })


def test_flags_concentration_and_industry():
    points = diagnosis.diagnose(_nav([1.0, 1.0]), _holdings([9.0] * 10), _industry())
    names = [p["metric"] for p in points]
    assert "前十大集中度" in names   # 90% > 60%
    assert "最大行业暴露" in names    # 86% > 50%


def test_no_flags_when_clean():
    points = diagnosis.diagnose(
        _nav([1.0, 1.1, 1.2]),
        _holdings([1.0] * 10),
        pd.DataFrame({"行业类别": ["制造业"], "占净值比例": [10.0], "市值": [100], "截止时间": ["2026-03-31"]}),
    )
    assert points == []
