"""回测工具。"""
from datetime import datetime, timedelta

from langchain_core.tools import tool

from src import backtest


@tool
def run_backtest(fund_code: str, strategy: str = "buy_hold", years: int = 3) -> str:
    """对基金跑一条历史回测，输出收益/回撤报告。
    strategy: buy_hold(买入持有) / dca(定投)。years: 回测年数。"""
    start = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
    result = backtest.run_backtest({"fund_code": fund_code, "strategy": strategy, "start": start})

    if "error" in result:
        return result["error"]

    m = result["metrics"]
    return (
        f"回测报告：{result['fund_code']} 策略[{result['strategy']}] 区间[{result['period']}]\n"
        f"- 投入本金：{m['投入本金']}\n"
        f"- 最终市值：{m['最终市值']}\n"
        f"- 总收益率：{m['总收益率%']}%\n"
        f"- 年化收益率：{m['年化收益率%']}%\n"
        f"- 最大回撤：{m['最大回撤%']}%\n"
        "（基于历史净值，不预测未来，仅供参考）"
    )
