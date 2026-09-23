"""每用户 LLM 调用额度：防脚本跑飞 / 误操作，额度放宽。

额度单位是「一次用户提问」（respond 入口），一次提问内部 goal loop 最多
max_steps 步 LLM 调用。Redis 挂时 incr 返回 0 → 放行（fail-open）。
"""
from datetime import datetime

from src.redis_client import incr

DAILY_LIMIT = 100   # 每用户每天
MINUTE_LIMIT = 10   # 每用户每分钟


def _keys(username: str) -> tuple[str, str]:
    """天 / 分钟两个固定窗口的 key。窗口边界由 key 名里的时间决定，TTL 仅作清理。"""
    now = datetime.now()
    day_key = f"quota:{username}:{now.strftime('%Y-%m-%d')}"
    min_key = f"quota:{username}:{now.strftime('%Y-%m-%d:%H:%M')}"
    return day_key, min_key


def consume(username: str) -> tuple[bool, str]:
    """消耗一次额度。返回 (是否放行, 拒绝时的提示)。"""
    day_key, min_key = _keys(username)
    min_count = incr(min_key, 60)
    day_count = incr(day_key, 86400)

    if min_count > MINUTE_LIMIT:
        return False, f"调用过于频繁，请稍后再试（每分钟最多 {MINUTE_LIMIT} 次）"
    if day_count > DAILY_LIMIT:
        return False, f"今日调用次数已达上限（{DAILY_LIMIT} 次），请明天再试"
    return True, ""
