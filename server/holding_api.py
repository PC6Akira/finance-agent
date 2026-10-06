"""持仓 + 推荐问题接口。"""
from fastapi import APIRouter, Depends, HTTPException

from server.deps import current_user
from server.schemas import AddHoldingIn, HoldingOut
from src import recommend, user

router = APIRouter(prefix="/api", tags=["holdings"])


@router.get("/holdings", response_model=list[HoldingOut])
def list_holdings(username: str = Depends(current_user)) -> list[dict]:
    return user.list_holdings(username)


@router.post("/holdings")
def add_holding(body: AddHoldingIn, username: str = Depends(current_user)) -> dict:
    ok, msg = user.add_holding(username, body.fund_code, body.amount, body.cost)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.delete("/holdings/{fund_code}")
def remove_holding(fund_code: str, username: str = Depends(current_user)) -> dict:
    user.remove_holding(username, fund_code.strip())
    return {"message": "已删除"}


@router.get("/recommend")
def recommend_questions(username: str = Depends(current_user)) -> dict:
    return {"questions": recommend.generate_questions(username)}
