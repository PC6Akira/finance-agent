"""基金数据 + 数据源测试接口。"""
import json
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from data_sources import fund as fund_ds
from data_sources import news as news_ds
from data_sources import search as search_ds
from server.deps import current_user
from src import backtest, diagnosis, metrics

router = APIRouter(prefix="/api", tags=["fund"])

YEAR = str(datetime.now().year)


def _df_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → JSON 记录列表（NaN/NaT → null，日期 → ISO 字符串）。"""
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", force_ascii=False, date_format="iso"))


def _nav_series(nav_df: pd.DataFrame) -> dict:
    return {
        "dates": nav_df["净值日期"].astype(str).tolist(),
        "nav": nav_df["单位净值"].astype(float).round(4).tolist(),
    }


def _industry_series(ind_df: pd.DataFrame) -> dict:
    if ind_df.empty:
        return {"labels": [], "weights": []}
    latest = ind_df[ind_df["截止时间"] == ind_df["截止时间"].max()]
    latest = latest.sort_values("占净值比例", ascending=True).tail(8)
    return {
        "labels": latest["行业类别"].astype(str).tolist(),
        "weights": latest["占净值比例"].astype(float).round(2).tolist(),
    }


def _top10_holdings(hold_df: pd.DataFrame) -> list[dict]:
    h = metrics.latest_quarter_holdings(hold_df).nlargest(10, "占净值比例")
    return [
        {"stock_code": str(r["股票代码"]), "stock_name": str(r["股票名称"]),
         "weight": float(r["占净值比例"])}
        for _, r in h.iterrows()
    ]


def _backtest_series(nav_df: pd.DataFrame) -> dict:
    recent = nav_df.tail(252 * 3)
    if recent.empty:
        return {"dates": [], "buy_hold": [], "dca": []}
    eh, ih = backtest.buy_hold(recent, {"initial_capital": 10000})
    ed, id_ = backtest.dca(recent, {"amount": 1000})
    return {
        "dates": recent["净值日期"].astype(str).tolist(),
        "buy_hold": ((eh / ih - 1) * 100).round(2).tolist(),
        "dca": ((ed / id_ - 1) * 100).round(2).tolist(),
    }


@router.get("/fund/{fund_code}")
def fund_detail(fund_code: str, username: str = Depends(current_user)) -> dict:
    """基金全景：净值 + 行业 + 前十大持仓 + 风险点 + 回测。"""
    fund_code = fund_code.strip()
    try:
        nav = fund_ds.get_fund_nav(fund_code)
        hold = fund_ds.get_fund_holdings(fund_code, YEAR)
        ind = fund_ds.get_fund_industry_allocation(fund_code, YEAR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据获取失败：{e}")

    return {
        "fund_code": fund_code,
        "nav": _nav_series(nav),
        "industry": _industry_series(ind),
        "holdings": _top10_holdings(hold),
        "risk_points": diagnosis.diagnose(nav, hold, ind),
        "backtest": _backtest_series(nav),
    }


# --- 数据源测试（原始 DataFrame → JSON 记录）---

def _fetch(fn) -> list[dict]:
    try:
        return _df_records(fn())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasource/nav/{fund_code}")
def ds_nav(fund_code: str, username: str = Depends(current_user)):
    return _fetch(lambda: fund_ds.get_fund_nav(fund_code.strip()))


@router.get("/datasource/holdings/{fund_code}")
def ds_holdings(fund_code: str, username: str = Depends(current_user)):
    return _fetch(lambda: fund_ds.get_fund_holdings(fund_code.strip(), YEAR))


@router.get("/datasource/industry/{fund_code}")
def ds_industry(fund_code: str, username: str = Depends(current_user)):
    return _fetch(lambda: fund_ds.get_fund_industry_allocation(fund_code.strip(), YEAR))


@router.get("/datasource/reports/{fund_code}")
def ds_reports(fund_code: str, username: str = Depends(current_user)):
    return _fetch(lambda: fund_ds.get_fund_reports(fund_code.strip()))


@router.get("/datasource/cls")
def ds_cls(username: str = Depends(current_user)):
    return _fetch(lambda: news_ds.get_cls_news()[["标题", "发布日期", "发布时间"]])


@router.get("/datasource/personnel/{fund_code}")
def ds_personnel(fund_code: str, username: str = Depends(current_user)):
    return _fetch(lambda: news_ds.get_fund_personnel_announcements(fund_code.strip()))


@router.get("/datasource/dividend/{fund_code}")
def ds_dividend(fund_code: str, username: str = Depends(current_user)):
    return _fetch(lambda: news_ds.get_fund_dividend_announcements(fund_code.strip()))


@router.get("/datasource/search")
def ds_search(q: str, username: str = Depends(current_user)):
    try:
        return search_ds.bocha_search(q, 5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
