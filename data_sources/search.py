"""通用搜索：博查 Bocha（国内免代理），用于基金经理访谈等开放式检索。"""
import hashlib

import requests

from src.cache import TTL_SEARCH, cached
from src.config import settings
from src.retry import retry_network

_URL = "https://api.bochaai.com/v1/web-search"


def _bocha_cache_key(query: str, count: int = 5) -> str:
    """query 是自然语言句子，可能很长/含特殊字符，故哈希后再作 key。"""
    qhash = hashlib.sha1(query.encode("utf-8")).hexdigest()[:16]
    return f"search:bocha:{qhash}:{count}"


@cached(key=_bocha_cache_key, ttl=TTL_SEARCH)
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
