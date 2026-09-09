"""Goal loop：目标 → [思考→行动→观察] 循环 → 终止/汇总。

用法：
    python -m src.loop "查一下基金 110022 的基本情况，用一句话汇总"
"""
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.config import settings
from src.guards.checks import register_guard_hooks
from src.hooks import trigger_hooks
from src.llm import get_llm
from tools.registry import call_tool, list_tools

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system.md"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _handle_tool_call(tc: dict, ask_user) -> str:
    """处理单个工具调用，返回要写入 ToolMessage 的内容。"""
    block = {"tool": tc["name"], "args": tc["args"]}
    result = trigger_hooks("PreToolUse", block)

    if result.kind == "forbid":  # ② 🔴 硬拦截
        return result.reason
    if result.kind == "require_permission":  # ③ 🟡 暂停问人
        ans = ask_user(f"{result.reason} 是否允许？(y/n): ")
        if ans.strip().lower() in ("y", "yes", "是"):
            return call_tool(tc["name"], tc["args"])
        return "用户拒绝执行该操作。"
    return call_tool(tc["name"], tc["args"])  # 🟢 放行


def run(goal: str, ask_user=input) -> str:
    """执行一个目标，返回带免责声明的最终结果。"""
    register_guard_hooks()

    messages = [
        SystemMessage(_load_system_prompt()),
        HumanMessage(goal),
    ]
    llm = get_llm().bind_tools(list_tools())

    for _ in range(settings.max_steps):
        resp = llm.invoke(messages)
        messages.append(resp)

        if not resp.tool_calls:  # ① 终止：模型给出最终回答
            return resp.content + "\n\n" + settings.disclaimer

        for tc in resp.tool_calls:
            content = _handle_tool_call(tc, ask_user)
            messages.append(ToolMessage(content=content, tool_call_id=tc["id"]))

    # ④ 达最大步数：强制汇总已有信息
    messages.append(HumanMessage(content="已达到最大步数，请基于已有信息给出最终汇总。"))
    final = llm.invoke(messages)
    return final.content + "\n\n" + settings.disclaimer


def main() -> None:
    goal = " ".join(sys.argv[1:]) or "查一下基金 110022 的基本情况，用一句话汇总"
    print(run(goal))


if __name__ == "__main__":
    main()
