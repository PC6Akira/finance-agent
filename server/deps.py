"""FastAPI 依赖：从 Authorization 头解析当前用户。"""
from fastapi import Header, HTTPException

from server.sessions import get_username


def current_user(authorization: str | None = Header(default=None)) -> str:
    """解析 `Authorization: Bearer <token>`，返回用户名；未登录抛 401。"""
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    username = get_username(token) if token else None
    if not username:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return username
