"""基金对比工具。"""
import pandas as pd
from langchain_core.tools import tool

from data_sources import fund as fund_ds
from src import metrics


@tool
def compare_funds(fund_codes: str) -> str:
    """横向对比多只基金（近1年收益/波动/回撤 + 持仓重叠）。
    fund_codes: 逗号分隔的基金代码，如 '110022,005827'。"""
    codes = [c.strip() for c in fund_codes.split(",") if c.strip()]
    if len(codes) < 2:
        return "至少需要 2 只基金代码（逗号分隔）。"

    rows, navs, holdings = [], {}, {}
    for c in codes:
        try:
            nav = fund_ds.get_fund_nav(c)
            hold = fund_ds.get_fund_holdings(c, "2024")
        except Exception as e:
            return f"拉取基金 {c} 数据失败：{e}"
        navs[c], holdings[c] = nav, hold
        recent = nav.tail(252)  # 近一年（约 252 个交易日）
        rows.append({
            "代码": c,
            "近1年收益%": round(metrics.period_return(recent), 2),
            "年化波动%": round(metrics.annualized_volatility(recent), 2),
            "最大回撤%": round(metrics.max_drawdown(recent), 2),
        })

    table = pd.DataFrame(rows).to_string(index=False)

    overlap_lines = []
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            common = metrics.holdings_overlap(holdings[codes[i]], holdings[codes[j]])
            overlap_lines.append(f"{codes[i]} vs {codes[j]}：{len(common)} 只共同重仓股 {common}")

    return f"基金对比（近一年）：\n{table}\n\n持仓重叠（最新季度）：\n" + "\n".join(overlap_lines)
