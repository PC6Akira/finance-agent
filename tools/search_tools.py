"""通用搜索工具：把 data_sources.search 包装成 tool。"""
from langchain_core.tools import tool

from data_sources.search import bocha_search
from tools._format import truncate


@tool
def search_web(query: str, count: int = 5) -> str:
    """通用网络搜索（博查），用于查基金经理访谈、行业观点等开放式信息。query: 搜索关键词。"""
    results = bocha_search(query, count)
    if not results:
        return "（未找到相关结果）"
    return "\n".join(f"- {r['title']}\n  {truncate(r['summary'], 120)}" for r in results)
