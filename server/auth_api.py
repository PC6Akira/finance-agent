"""鉴权接口：注册 / 登录 / 登出 / 当前用户。"""
from fastapi import APIRouter, Depends, Header, HTTPException

from server.deps import current_user
from server.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from server.sessions import create_session, delete_session
from src import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(body: RegisterIn) -> dict:
    ok, msg = auth.register(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn) -> TokenOut:
    ok, msg = auth.login(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=401, detail=msg)
    return TokenOut(token=create_session(body.username), username=body.username)


@router.post("/logout")
def logout(username: str = Depends(current_user),
           authorization: str | None = Header(default=None)) -> dict:
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    delete_session(token)
    return {"message": "已退出登录"}


@router.get("/me", response_model=UserOut)
def me(username: str = Depends(current_user)) -> UserOut:
    return UserOut(username=username)
