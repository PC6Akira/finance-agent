"""对话接口：goal loop 一问一答（同步返回完整回答）。"""
from fastapi import APIRouter, Depends, HTTPException

from server.deps import current_user
from server.schemas import ChatIn, ChatOut
from src import quota, user
from src.loop import run

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn, username: str = Depends(current_user)) -> ChatOut:
    """执行一轮 goal loop，返回带免责声明的最终回答。"""
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    ok, quota_msg = quota.consume(username)
    if not ok:
        raise HTTPException(status_code=429, detail=quota_msg)

    past = user.recent_messages(username, limit=20)  # 最近 10 轮
    # Web 下无交互终端：🟡 需许可的工具一律拒绝，绝不阻塞 input()
    reply = run(message, history=past, ask_user=lambda _: "否")
    user.add_message(username, "user", message)
    user.add_message(username, "assistant", reply)
    return ChatOut(reply=reply)
