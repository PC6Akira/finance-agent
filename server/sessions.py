"""会话 token 存储：Redis 为主，内存镜像兜底（Redis 挂时仍可登录）。

和项目里其它 Redis 用法一致——Redis 是加速层不是故障点，这里同样 fail-open：
Redis 不可用时 token 落在进程内存，登录 / 鉴权照常工作，仅重启进程后失效。
"""
import secrets
import time

from src.redis_client import delete, get, put

SESSION_TTL = 7 * 24 * 3600  # 7 天（秒）

# 内存镜像：token -> (username, 过期时间戳)。仅作 Redis 挂时的兜底。
_mem: dict[str, tuple[str, float]] = {}


def _prune() -> None:
    """清理已过期的内存 token，防无限增长。"""
    now = time.time()
    for token in [t for t, (_, exp) in _mem.items() if exp < now]:
        _mem.pop(token, None)


def create_session(username: str) -> str:
    """签发不透明 token，返回 token 字符串。"""
    token = secrets.token_urlsafe(32)
    put(f"auth:token:{token}", username, SESSION_TTL)
    _mem[token] = (username, time.time() + SESSION_TTL)
    _prune()
    return token


def get_username(token: str | None) -> str | None:
    """按 token 取用户名；未登录 / 过期 / 无效返回 None。"""
    if not token:
        return None
    username = get(f"auth:token:{token}")
    if username:
        return username
    entry = _mem.get(token)  # Redis 挂或未命中 → 查内存镜像兜底
    if entry and entry[1] >= time.time():
        return entry[0]
    return None


def delete_session(token: str) -> None:
    """登出：删除 token（Redis + 内存镜像）。"""
    if not token:
        return
    delete(f"auth:token:{token}")
    _mem.pop(token, None)
