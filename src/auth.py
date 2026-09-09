"""用户认证：注册 / 登录（bcrypt 哈希，不存明文）。"""
from datetime import datetime

import bcrypt
from sqlalchemy import select

from db.database import SessionLocal
from db.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def register(username: str, password: str) -> tuple[bool, str]:
    """注册。返回 (是否成功, 提示)。"""
    username = username.strip()
    if not username or not password:
        return False, "用户名和密码不能为空"
    with SessionLocal() as s:
        if s.scalar(select(User).where(User.username == username)):
            return False, "用户名已存在"
        s.add(User(
            username=username,
            password_hash=hash_password(password),
            created_at=datetime.now().isoformat(),
        ))
        s.commit()
    return True, "注册成功，请登录"


def login(username: str, password: str) -> tuple[bool, str]:
    """登录。返回 (是否成功, 提示)。"""
    username = username.strip()
    with SessionLocal() as s:
        user = s.scalar(select(User).where(User.username == username))
        if user is None:
            return False, "用户不存在"
        if verify_password(password, user.password_hash):
            return True, "登录成功"
        return False, "密码错误"
