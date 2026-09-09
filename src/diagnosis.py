"""持仓诊断：集中度 / 行业暴露 / 风格漂移 → 风险点（只提示，不下结论）。"""
from src import metrics

# 风险阈值（可调）
TOP10_THRESHOLD = 60.0        # 前十大集中度（%）
SINGLE_STOCK_THRESHOLD = 9.0  # 最大单一持仓（%）
INDUSTRY_THRESHOLD = 50.0     # 最大行业暴露（%）
DRIFT_THRESHOLD = 10.0        # 行业配置漂移（百分点）
DRAWDOWN_THRESHOLD = -20.0    # 最大回撤（%）


def top10_concentration(holdings_df) -> float:
    """前十大重仓股合计占净值比例（%）。"""
    h = metrics.latest_quarter_holdings(holdings_df)
    if h.empty:
        return 0.0
    return float(h["占净值比例"].astype(float).nlargest(10).sum())


def max_single_stock(holdings_df) -> float:
    """最大单一持仓占净值比例（%）。"""
    h = metrics.latest_quarter_holdings(holdings_df)
    if h.empty:
        return 0.0
    return float(h["占净值比例"].astype(float).max())


def max_industry(industry_df) -> tuple[str, float]:
    """最新报告期最大行业及其占比（%）。"""
    if industry_df.empty:
        return "", 0.0
    latest = industry_df["截止时间"].max()
    latest_df = industry_df[industry_df["截止时间"] == latest]
    row = latest_df.loc[latest_df["占净值比例"].astype(float).idxmax()]
    return str(row["行业类别"]), float(row["占净值比例"])


def industry_drift(industry_df) -> float:
    """首末两个报告期，最大行业占比之差（百分点）。"""
    if industry_df.empty:
        return 0.0
    dates = sorted(industry_df["截止时间"].unique())
    if len(dates) < 2:
        return 0.0
    first = industry_df[industry_df["截止时间"] == dates[0]]["占净值比例"].astype(float).max()
    last = industry_df[industry_df["截止时间"] == dates[-1]]["占净值比例"].astype(float).max()
    return float(last - first)


def diagnose(nav_df, holdings_df, industry_df) -> list[dict]:
    """生成风险点清单，每条 {metric, value, risk}。只陈述事实 + 提示风险，不下结论。"""
    points = []

    top10 = top10_concentration(holdings_df)
    if top10 >= TOP10_THRESHOLD:
        points.append({"metric": "前十大集中度", "value": f"{top10:.1f}%", "risk": "持仓集中度偏高"})

    single = max_single_stock(holdings_df)
    if single >= SINGLE_STOCK_THRESHOLD:
        points.append({"metric": "最大单一持仓", "value": f"{single:.1f}%", "risk": "单一股票占比偏高"})

    ind_name, ind_weight = max_industry(industry_df)
    if ind_weight >= INDUSTRY_THRESHOLD:
        points.append({"metric": "最大行业暴露", "value": f"{ind_name} {ind_weight:.1f}%", "risk": "行业集中度极高"})

    drift = industry_drift(industry_df)
    if abs(drift) >= DRIFT_THRESHOLD:
        points.append({"metric": "行业配置漂移", "value": f"{drift:+.1f}pp", "risk": "行业配置变动较大"})

    dd = metrics.max_drawdown(nav_df.tail(252))
    if dd <= DRAWDOWN_THRESHOLD:
        points.append({"metric": "近1年最大回撤", "value": f"{dd:.1f}%", "risk": "历史回撤较大"})

    return points
