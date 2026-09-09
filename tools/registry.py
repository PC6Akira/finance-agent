"""工具注册表：收集所有工具，暴露 list_tools() 和 call_tool()。

循环只依赖本模块的接口，不 import 任何具体工具。
"""
from langchain_core.tools import BaseTool

from tools.fund_tools import (
    get_fund_holdings,
    get_fund_industry_allocation,
    get_fund_nav,
    get_fund_reports,
)
from tools.backtest_tools import run_backtest
from tools.compare_tools import compare_funds
from tools.diagnose_tools import diagnose_fund
from tools.news_tools import get_finance_news, get_fund_personnel_announcements
from tools.search_tools import search_web

_TOOLS: dict[str, BaseTool] = {
    t.name: t
    for t in [
        get_fund_nav,
        get_fund_holdings,
        get_fund_industry_allocation,
        get_fund_reports,
        get_finance_news,
        get_fund_personnel_announcements,
        search_web,
        compare_funds,
        diagnose_fund,
        run_backtest,
    ]
}


def list_tools() -> list[BaseTool]:
    """返回所有工具对象（供 bind_tools 生成 schema）。"""
    return list(_TOOLS.values())


def call_tool(name: str, args: dict) -> str:
    """按名调用工具，返回结果字符串。"""
    tool = _TOOLS.get(name)
    if tool is None:
        return f"未知工具：{name}"
    return str(tool.invoke(args))
