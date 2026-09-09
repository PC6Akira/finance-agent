"""回测编排：配置 → 数据 → 策略 → 结果 → 报告。

策略可插拔：用 @register_strategy 注册新策略，返回 (净值曲线, 投入本金)。
"""
import pandas as pd

from data_sources import fund as fund_ds

STRATEGIES: dict = {}


def register_strategy(name: str):
    def deco(fn):
        STRATEGIES[name] = fn
        return fn
    return deco


@register_strategy("buy_hold")
def buy_hold(nav_df: pd.DataFrame, params: dict) -> tuple[pd.Series, float]:
    """买入持有：期初一次性买入，全程持有。"""
    initial = float(params.get("initial_capital", 10000))
    nav = nav_df["单位净值"].astype(float)
    equity = nav / nav.iloc[0] * initial
    return equity, initial


@register_strategy("dca")
def dca(nav_df: pd.DataFrame, params: dict) -> tuple[pd.Series, float]:
    """定投：每月第一个交易日投入固定金额。"""
    amount = float(params.get("amount", 1000))
    nav = nav_df["单位净值"].astype(float)
    dates = pd.to_datetime(nav_df["净值日期"])
    shares, invested, prev_month = 0.0, 0.0, None
    equity = []
    for d, v in zip(dates, nav):
        month = (d.year, d.month)
        if month != prev_month:  # 每月首个交易日定投
            shares += amount / v
            invested += amount
            prev_month = month
        equity.append(shares * v)
    return pd.Series(equity, index=dates), invested


def compute_metrics(equity: pd.Series, invested: float) -> dict:
    """从净值曲线算结果指标。"""
    final_value = float(equity.iloc[-1])
    total_return = (final_value - invested) / invested * 100
    years = len(equity) / 252
    annualized = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0.0
    dd = (equity - equity.cummax()) / equity.cummax()
    return {
        "最终市值": round(final_value, 2),
        "投入本金": round(invested, 2),
        "总收益率%": round(total_return, 2),
        "年化收益率%": round(annualized, 2),
        "最大回撤%": round(float(dd.min() * 100), 2),
    }


def run_backtest(config: dict) -> dict:
    """编排：配置 → 数据 → 策略 → 结果。"""
    fund_code = config["fund_code"]
    strategy_name = config.get("strategy", "buy_hold")
    params = config.get("params", {})

    nav_df = fund_ds.get_fund_nav(fund_code)
    start, end = config.get("start"), config.get("end")
    if start or end:
        dates = pd.to_datetime(nav_df["净值日期"])
        mask = pd.Series(True, index=nav_df.index)
        if start:
            mask &= dates >= pd.to_datetime(start)
        if end:
            mask &= dates <= pd.to_datetime(end)
        nav_df = nav_df[mask]
    if nav_df.empty:
        return {"error": f"基金 {fund_code} 无净值数据"}

    strategy = STRATEGIES.get(strategy_name)
    if strategy is None:
        return {"error": f"未知策略：{strategy_name}（可选：{', '.join(STRATEGIES)}）"}

    equity, invested = strategy(nav_df, params)
    return {
        "fund_code": fund_code,
        "strategy": strategy_name,
        "period": f"{nav_df['净值日期'].iloc[0]} ~ {nav_df['净值日期'].iloc[-1]}",
        "metrics": compute_metrics(equity, invested),
    }
