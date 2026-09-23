"""Redis 客户端：缓存 + 限流计数器的统一入口。

Redis 是加速层，不是故障点——连接失败/超时一律降级：
- 读缓存返回 None（上层当作 miss，业务直连上游）
- 写缓存静默失败；计数返回 0（限流降级为放行）
所有降级只记 warning 日志，不抛异常、不阻塞业务。
"""
import redis

from src.config import settings
from src.logger import get_logger

logger = get_logger("redis")

# decode_responses=True：get 返回 str 而非 bytes；短超时保证 Redis 挂掉时快速降级
_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def _safe(fn, default=None):
    """执行 Redis 操作；任何异常都降级为 default 并记日志。"""
    try:
        return fn()
    except Exception as exc:  # 降级兜底，吞掉一切 Redis 异常，业务不因此中断
        logger.warning("Redis 不可用，已降级：%s", exc)
        return default


def get(key: str) -> str | None:
    """读字符串。未命中或 Redis 挂都返回 None（上层当作缓存 miss）。"""
    return _safe(lambda: _client.get(key))


def put(key: str, value: str, ttl: int) -> None:
    """写字符串并设 TTL（秒）。Redis 挂则静默失败。"""
    _safe(lambda: _client.set(key, value, ex=ttl))


def incr(key: str, ttl: int) -> int:
    """原子自增，TTL 仅在 key 首次创建时设置（EXPIRE NX，固定窗口）。

    Redis 挂时返回 0——限流调用方拿 0 去比较上限，天然放行（fail-open）。
    """
    def _do() -> int:
        count = _client.incr(key)
        # 仅当 key 尚无过期时间时设置，避免每次自增都刷新窗口
        _client.expire(key, ttl, nx=True)
        return int(count)

    return _safe(_do, default=0)
