"""资讯数据源：akshare 封装（舆情 / 基金公告）。"""
import akshare as ak
import pandas as pd


def get_cls_news() -> pd.DataFrame:
    """财联社电报（最新财经快讯 / 舆情）。"""
    return ak.stock_info_global_cls(symbol="全部")


def get_fund_dividend_announcements(fund_code: str) -> pd.DataFrame:
    """基金分红公告。"""
    return ak.fund_announcement_dividend_em(symbol=fund_code)


def get_fund_personnel_announcements(fund_code: str) -> pd.DataFrame:
    """基金人事公告（基金经理变动等）。"""
    return ak.fund_announcement_personnel_em(symbol=fund_code)
