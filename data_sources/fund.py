"""基金数据源：akshare 封装（净值 / 持仓 / 季报）。"""
import akshare as ak
import pandas as pd

from src.retry import retry_network


@retry_network
def get_fund_nav(fund_code: str) -> pd.DataFrame:
    """单位净值走势。列：净值日期 / 单位净值 / 日增长率。"""
    return ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")


@retry_network
def get_fund_holdings(fund_code: str, year: str) -> pd.DataFrame:
    """季度重仓股持仓。year 如 '2024'。"""
    return ak.fund_portfolio_hold_em(symbol=fund_code, date=year)


@retry_network
def get_fund_industry_allocation(fund_code: str, year: str) -> pd.DataFrame:
    """季报·行业配置（占净值比例 / 市值，按季度）。year 如 '2024'。"""
    return ak.fund_portfolio_industry_allocation_em(symbol=fund_code, date=year)


@retry_network
def get_fund_reports(fund_code: str) -> pd.DataFrame:
    """季报 / 年报等定期报告公告列表。"""
    return ak.fund_announcement_report_em(symbol=fund_code)
