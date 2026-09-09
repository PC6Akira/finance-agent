"""资讯工具：把 data_sources.news 包装成 tool。"""
from langchain_core.tools import tool

from data_sources import news as news_ds
from tools._format import df_to_str


@tool
def get_finance_news() -> str:
    """获取最新财经快讯 / 舆情（财联社电报）。无参数。"""
    df = news_ds.get_cls_news()
    sub = df[["标题", "发布日期", "发布时间"]].head(10)
    return f"财联社电报（最新 10 条）：\n{df_to_str(sub, 10)}"


@tool
def get_fund_personnel_announcements(fund_code: str) -> str:
    """查询基金经理变更等人事公告。fund_code: 6 位基金代码。"""
    df = news_ds.get_fund_personnel_announcements(fund_code)
    sub = df[["公告标题", "公告日期"]].head(10)
    return f"人事公告（最新 10 条）：\n{df_to_str(sub, 10)}"
