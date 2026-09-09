"""通用搜索：博查 Bocha（国内免代理），用于基金经理访谈等开放式检索。"""
import requests

from src.config import settings
from src.retry import retry_network

_URL = "https://api.bochaai.com/v1/web-search"


@retry_network
def bocha_search(query: str, count: int = 5) -> list[dict]:
    """按关键词搜索，返回 [{title, url, summary, site, date}]。"""
    headers = {
        "Authorization": f"Bearer {settings.bocha_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"query": query, "count": count, "freshness": "noLimit", "summary": True}
    resp = requests.post(_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("data", {}).get("webPages", {}).get("value", [])
    return [
        {
            "title": item.get("name"),
            "url": item.get("url"),
            "summary": item.get("summary") or item.get("snippet"),
            "site": item.get("siteName"),
            "date": item.get("datePublished"),
        }
        for item in items
    ]
