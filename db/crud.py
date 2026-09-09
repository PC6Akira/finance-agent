"""CRUD：DataFrame 落库 + 查询。"""
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from db.database import SessionLocal
from db.models import (
    Fund,
    FundAnnouncement,
    FundHolding,
    FundIndustryAllocation,
    FundNav,
)


def _upsert(model, rows: list[dict]) -> None:
    """INSERT OR IGNORE：按主键去重，重复拉取不产生脏数据。"""
    if not rows:
        return
    stmt = sqlite_insert(model).on_conflict_do_nothing()
    with SessionLocal() as s:
        s.execute(stmt, rows)
        s.commit()


def save_fund(code: str, name: str = None, manager: str = None, company: str = None) -> None:
    _upsert(Fund, [{"code": code, "name": name, "manager": manager, "company": company}])


def save_fund_nav(fund_code: str, df) -> None:
    _upsert(FundNav, [
        {"fund_code": fund_code, "nav_date": str(r["净值日期"]), "unit_nav": r["单位净值"], "daily_return": r["日增长率"]}
        for r in df.to_dict("records")
    ])


def save_fund_holdings(fund_code: str, df) -> None:
    _upsert(FundHolding, [
        {
            "fund_code": fund_code,
            "quarter": r["季度"],
            "stock_code": r["股票代码"],
            "stock_name": r["股票名称"],
            "weight": r["占净值比例"],
            "shares": r["持股数"],
            "market_value": r["持仓市值"],
        }
        for r in df.to_dict("records")
    ])


def save_fund_industry_allocation(fund_code: str, df) -> None:
    _upsert(FundIndustryAllocation, [
        {
            "fund_code": fund_code,
            "report_date": str(r["截止时间"]),
            "industry": r["行业类别"],
            "weight": r["占净值比例"],
            "market_value": r["市值"],
        }
        for r in df.to_dict("records")
    ])


def save_fund_announcements(fund_code: str, ann_type: str, df) -> None:
    _upsert(FundAnnouncement, [
        {
            "id": r["报告ID"],
            "fund_code": fund_code,
            "ann_type": ann_type,
            "title": r["公告标题"],
            "publish_date": str(r["公告日期"]),
        }
        for r in df.to_dict("records")
    ])


# --- 查询 ---

def count_fund_nav(fund_code: str) -> int:
    with SessionLocal() as s:
        return len(s.scalars(select(FundNav).where(FundNav.fund_code == fund_code)).all())


def count_fund_holdings(fund_code: str) -> int:
    with SessionLocal() as s:
        return len(s.scalars(select(FundHolding).where(FundHolding.fund_code == fund_code)).all())


def count_industry(fund_code: str) -> int:
    with SessionLocal() as s:
        return len(s.scalars(select(FundIndustryAllocation).where(FundIndustryAllocation.fund_code == fund_code)).all())


def count_announcements(fund_code: str) -> int:
    with SessionLocal() as s:
        return len(s.scalars(select(FundAnnouncement).where(FundAnnouncement.fund_code == fund_code)).all())


def latest_nav(fund_code: str) -> FundNav:
    with SessionLocal() as s:
        return s.scalars(
            select(FundNav).where(FundNav.fund_code == fund_code).order_by(FundNav.nav_date.desc()).limit(1)
        ).first()
