"""工具注册表：收集所有工具，暴露 list_tools() 和 call_tool()。

循环只依赖本模块的接口，不 import 任何具体工具。
"""
from langchain_core.tools import BaseTool

from tools.placeholders import get_mock_fund_profile, get_mock_fund_risk

_TOOLS: dict[str, BaseTool] = {
    t.name: t
    for t in [get_mock_fund_profile, get_mock_fund_risk]
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
