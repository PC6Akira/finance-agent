"""用户持仓 + 对话历史。"""
from datetime import datetime

from sqlalchemy import select

from data_sources import fund as fund_ds
from db.database import SessionLocal
from db.models import Message, UserHolding


def _fund_name(fund_code: str) -> str:
    """查基金名，失败则返回代码。"""
    try:
        reports = fund_ds.get_fund_reports(fund_code)
        if not reports.empty:
            return str(reports["基金名称"].iloc[0])
    except Exception:
        pass
    return fund_code


def add_holding(username: str, fund_code: str, amount: float, cost: float | None = None) -> tuple[bool, str]:
    """添加持仓。返回 (是否成功, 提示)。"""
    fund_code = fund_code.strip()
    if not fund_code or not amount or amount <= 0:
        return False, "请填写基金代码和持有金额"
    name = _fund_name(fund_code)
    with SessionLocal() as s:
        s.add(UserHolding(
            username=username, fund_code=fund_code, fund_name=name,
            amount=amount, cost=cost, created_at=datetime.now().isoformat(),
        ))
        s.commit()
    return True, f"已添加：{name}（{fund_code}）"


def list_holdings(username: str) -> list[dict]:
    """列出用户持仓。"""
    with SessionLocal() as s:
        rows = s.scalars(select(UserHolding).where(UserHolding.username == username).order_by(UserHolding.id)).all()
    return [{"fund_code": r.fund_code, "fund_name": r.fund_name, "amount": r.amount, "cost": r.cost} for r in rows]


def remove_holding(username: str, fund_code: str) -> None:
    with SessionLocal() as s:
        rows = s.scalars(select(UserHolding).where(
            UserHolding.username == username, UserHolding.fund_code == fund_code
        )).all()
        for r in rows:
            s.delete(r)
        s.commit()


def add_message(username: str, role: str, content: str) -> None:
    with SessionLocal() as s:
        s.add(Message(username=username, role=role, content=content, created_at=datetime.now().isoformat()))
        s.commit()


def recent_messages(username: str, limit: int = 20) -> list[tuple[str, str]]:
    """最近 limit 条消息（按时间正序），返回 [(role, content)]。"""
    with SessionLocal() as s:
        rows = s.scalars(select(Message).where(Message.username == username).order_by(Message.id.desc()).limit(limit)).all()
    rows = list(rows)[::-1]
    return [(r.role, r.content) for r in rows]
