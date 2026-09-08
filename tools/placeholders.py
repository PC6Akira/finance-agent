"""占位工具（T4 演示循环用，T5-T7 替换为真实工具）。"""
from langchain_core.tools import tool

_MOCK_PROFILE = {
    "110022": "易方达消费行业股票：偏消费白马，重仓白酒、家电。",
    "005827": "易方达蓝筹精选混合：白酒 + 互联网龙头，大盘蓝筹。",
}

_MOCK_RISK = {
    "110022": "行业集中度偏高（白酒占比过半），历史回撤较大。",
    "005827": "前十大重仓集中度较高，受白酒板块波动影响明显。",
}


@tool
def get_mock_fund_profile(fund_code: str) -> str:
    """获取基金的基本信息与投资风格（占位数据，后续接真实 akshare）。

    Args:
        fund_code: 6 位基金代码，例如 110022
    """
    return _MOCK_PROFILE.get(fund_code, f"（占位）未收录基金 {fund_code} 的模拟信息。")


@tool
def get_mock_fund_risk(fund_code: str) -> str:
    """获取基金的主要风险点（占位数据，后续接真实诊断）。

    Args:
        fund_code: 6 位基金代码，例如 110022
    """
    return _MOCK_RISK.get(fund_code, f"（占位）未收录基金 {fund_code} 的模拟风险点。")
