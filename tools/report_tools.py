"""信息汇总工具。"""
from langchain_core.tools import tool

from src import report


@tool
def report_fund(fund_code: str) -> str:
    """生成基金的完整投研简报（概况 / 业绩 / 持仓 / 风险点 / 近期公告）。fund_code: 6 位基金代码。"""
    return report.build_report(fund_code)
