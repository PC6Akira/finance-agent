"""基金数据工具：把 data_sources.fund 包装成 LLM 可调用的 tool。"""
from datetime import datetime

from langchain_core.tools import tool

from data_sources import fund as fund_ds
from tools._format import df_to_str

_DEFAULT_YEAR = str(datetime.now().year)


@tool
def get_fund_nav(fund_code: str) -> str:
    """查询基金单位净值走势，看最新净值和近期涨跌。fund_code: 6 位基金代码，如 110022。"""
    df = fund_ds.get_fund_nav(fund_code)
    return f"单位净值走势（最新 10 条，共 {len(df)} 条）：\n{df_to_str(df.tail(10))}"


@tool
def get_fund_holdings(fund_code: str, year: str = _DEFAULT_YEAR) -> str:
    """查询基金季度重仓股持仓（占净值比例、市值）。year: 年份，如 '2024'。"""
    df = fund_ds.get_fund_holdings(fund_code, year)
    return f"重仓股持仓（前 10 条）：\n{df_to_str(df, 10)}"


@tool
def get_fund_industry_allocation(fund_code: str, year: str = _DEFAULT_YEAR) -> str:
    """查询基金季报的行业配置（各行业占净值比例）。year: 年份，如 '2024'。"""
    df = fund_ds.get_fund_industry_allocation(fund_code, year)
    return f"行业配置（前 10 条）：\n{df_to_str(df, 10)}"


@tool
def get_fund_reports(fund_code: str) -> str:
    """查询基金的定期报告（季报/年报）公告列表。fund_code: 6 位基金代码。"""
    df = fund_ds.get_fund_reports(fund_code)
    sub = df[["公告标题", "公告日期"]].sort_values("公告日期", ascending=False).head(10)
    return f"定期报告公告（最新 10 条）：\n{df_to_str(sub, 10)}"
