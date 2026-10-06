"""Pydantic 请求 / 响应模型。"""
from pydantic import BaseModel


class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    token: str
    username: str


class UserOut(BaseModel):
    username: str


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str


class AddHoldingIn(BaseModel):
    fund_code: str
    amount: float
    cost: float | None = None


class HoldingOut(BaseModel):
    fund_code: str
    fund_name: str | None = None
    amount: float | None = None
    cost: float | None = None
