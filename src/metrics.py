"""基金指标计算：收益率、波动率、最大回撤、持仓重叠。"""
import numpy as np
import pandas as pd


def period_return(nav_df: pd.DataFrame) -> float:
    """区间收益率（%）。nav_df 需含『单位净值』列，按日期升序。"""
    if nav_df.empty:
        return 0.0
    nav = nav_df["单位净值"].astype(float)
    return float((nav.iloc[-1] / nav.iloc[0] - 1) * 100)


def annualized_volatility(nav_df: pd.DataFrame) -> float:
    """年化波动率（%），基于日增长率（%）序列。"""
    if nav_df.empty:
        return 0.0
    rets = nav_df["日增长率"].astype(float) / 100
    return float(rets.std() * np.sqrt(252) * 100)


def max_drawdown(nav_df: pd.DataFrame) -> float:
    """最大回撤（%），基于单位净值曲线。"""
    if nav_df.empty:
        return 0.0
    nav = nav_df["单位净值"].astype(float).to_numpy()
    peak = np.maximum.accumulate(nav)
    dd = (nav - peak) / peak
    return float(dd.min() * 100)


def latest_quarter_holdings(holdings_df: pd.DataFrame) -> pd.DataFrame:
    """取最新季度的持仓。"""
    if holdings_df.empty:
        return holdings_df
    latest = holdings_df["季度"].max()
    return holdings_df[holdings_df["季度"] == latest]


def holdings_overlap(holdings_a: pd.DataFrame, holdings_b: pd.DataFrame) -> list[str]:
    """两只基金共同的重仓股代码（按最新季度比较）。"""
    a = latest_quarter_holdings(holdings_a)
    b = latest_quarter_holdings(holdings_b)
    if a.empty or b.empty:
        return []
    return sorted(set(a["股票代码"].astype(str)) & set(b["股票代码"].astype(str)))
