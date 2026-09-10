"""Goal loop：目标 → [思考→行动→观察] 循环 → 终止/汇总。

用法：
    python -m src.loop "查一下基金 110022 的基本情况，用一句话汇总"
"""
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.config import settings
from src.guards.checks import register_guard_hooks
from src.hooks import trigger_hooks
from src.llm import get_llm
from src.logger import get_logger
from src.output import finalize
from src.verify import verify_and_correct
from tools.registry import call_tool, list_tools

logger = get_logger(__name__)
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system.md"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _call_tool_safe(name: str, args: dict) -> str:
    """调用工具并兜底异常：失败时记录日志、返回错误信息而非崩溃。"""
    try:
        return call_tool(name, args)
    except Exception as e:
        logger.error(f"工具调用失败 {name}({args}): {e}")
        return f"工具调用失败：{e}"


def _handle_tool_call(tc: dict, ask_user) -> str:
    """处理单个工具调用，返回要写入 ToolMessage 的内容。"""
    block = {"tool": tc["name"], "args": tc["args"]}
    result = trigger_hooks("PreToolUse", block)

    if result.kind == "forbid":  # ② 🔴 硬拦截
        return result.reason
    if result.kind == "require_permission":  # ③ 🟡 暂停问人
        ans = ask_user(f"{result.reason} 是否允许？(y/n): ")
        if ans.strip().lower() in ("y", "yes", "是"):
            return _call_tool_safe(tc["name"], tc["args"])
        return "用户拒绝执行该操作。"
    return _call_tool_safe(tc["name"], tc["args"])  # 🟢 放行


def run(goal: str, history: list[tuple[str, str]] | None = None, ask_user=input) -> str:
    """执行一个目标（可带多轮对话历史），返回带免责声明的最终结果。"""
    register_guard_hooks()
    logger.info(f"任务开始：{goal[:80]}")

    messages = [SystemMessage(_load_system_prompt())]
    for role, content in (history or []):
        messages.append(HumanMessage(content) if role == "user" else AIMessage(content))
    messages.append(HumanMessage(goal))
    llm = get_llm().bind_tools(list_tools())

    tool_outputs = []  # 本轮工具返回，供事实校验
    for _ in range(settings.max_steps):
        resp = llm.invoke(messages)
        messages.append(resp)

        if not resp.tool_calls:  # ① 终止：模型给出最终回答
            logger.info("任务完成（模型给出最终回答）")
            return finalize(verify_and_correct(resp.content, tool_outputs))

        for tc in resp.tool_calls:
            logger.info(f"调用工具：{tc['name']}")
            content = _handle_tool_call(tc, ask_user)
            tool_outputs.append((tc["name"], content))
            messages.append(ToolMessage(content=content, tool_call_id=tc["id"]))

    # ④ 达最大步数：强制汇总已有信息
    logger.warning(f"达到最大步数 {settings.max_steps}，强制汇总")
    messages.append(HumanMessage(content="已达到最大步数，请基于已有信息给出最终汇总。"))
    final = llm.invoke(messages)
    return finalize(verify_and_correct(final.content, tool_outputs))


def main() -> None:
    goal = " ".join(sys.argv[1:]) or "查一下基金 110022 的基本情况，用一句话汇总"
    print(run(goal))


if __name__ == "__main__":
    main()
