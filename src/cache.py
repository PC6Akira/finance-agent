"""akshare 数据缓存：Redis String 存 JSON，TTL 自动过期匹配数据新鲜度。

用法：给 data_sources 里的函数套 @cached(key=..., ttl=...)。
- key 为字符串时支持 {参数名} 占位符，如 "fund:nav:{fund_code}"
- key 也可传函数自定义（如对 query 做哈希，见 search.py）
缓存 miss / Redis 挂 / 序列化失败，都会直连上游，缓存层绝不阻断业务。
"""
import functools
import inspect
import json

import pandas as pd

from src.logger import get_logger
from src.redis_client import get, put

logger = get_logger("cache")

# TTL（秒）——按数据新鲜度分档（见 REDIS.md 第 1 条）
TTL_NAV = 6 * 3600         # 基金净值：每日更新
TTL_HOLDINGS = 2 * 86400   # 持仓 / 行业配置：每季度
TTL_ANNOUNCE = 3600        # 公告 / 分红 / 人事：分钟~小时
TTL_NEWS = 20 * 60         # 舆情（财联社）：分钟级
TTL_SEARCH = 3600          # 博查搜索：小时级


def _serialize(value) -> str:
    """DataFrame → orient=table（保留 dtype）；其余（list/dict）→ json.dumps。"""
    if isinstance(value, pd.DataFrame):
        data = value.to_json(orient="table", date_format="iso", force_ascii=False)
        return json.dumps({"type": "df", "data": data}, ensure_ascii=False)
    return json.dumps({"type": "json", "data": value}, ensure_ascii=False, default=str)


def _deserialize(text: str):
    """按类型标记还原返回值。"""
    envelope = json.loads(text)
    if envelope["type"] == "df":
        return pd.read_json(envelope["data"], orient="table")
    return envelope["data"]


def cached(key, ttl: int):
    """缓存装饰器。key 为字符串时按 {参数名} 占位符格式化，为函数时直接调用。"""

    def deco(fn):
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            cache_key = (
                key.format(**bound.arguments)
                if isinstance(key, str)
                else key(**bound.arguments)
            )

            text = get(cache_key)
            if text is not None:
                try:
                    return _deserialize(text)
                except Exception as exc:
                    logger.warning("缓存反序列化失败，直连上游（%s）：%s", cache_key, exc)

            result = fn(*args, **kwargs)
            try:
                put(cache_key, _serialize(result), ttl)
            except Exception as exc:
                logger.warning("缓存写入失败，跳过缓存（%s）：%s", cache_key, exc)
            return result

        return wrapper

    return deco
