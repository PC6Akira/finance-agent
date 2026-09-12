"""事实锚定 verifier：校验 LLM 回答里的事实是否来自工具返回（抓编造 / 错配）。"""
import json

from src.llm import get_llm
from src.logger import get_logger

logger = get_logger(__name__)

MAX_PER_TOOL = 1500   # 单个工具返回截断
MAX_TOTAL = 6000      # 喂给校验器的数据总量上限


def _format_tool_outputs(tool_outputs: list[tuple[str, str]]) -> str:
    lines, total = [], 0
    for name, content in tool_outputs:
        chunk = f"=== {name} ===\n{content[:MAX_PER_TOOL]}"
        total += len(chunk)
        if total > MAX_TOTAL:
            break
        lines.append(chunk)
    return "\n\n".join(lines)


def _strip_fences(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def _check(answer: str, data_text: str) -> tuple[bool, list[str]]:
    prompt = f"""你是事实校验器。核对【回答】里的每个事实性陈述（具体数值、基金代码/名称、日期、指标名）能否在【工具数据】里找到一致支撑。

判据：
- 编造：数值/事实在工具数据里完全不存在 → 记问题；
- 错配：数值存在，但对应的基金或指标名对不上 → 记问题；
- 允许合理的四舍五入/约等，明显不符才记问题。
只校验事实，不校验推理、解读、结论、建议。

【工具数据】
{data_text}

【回答】
{answer}

严格输出 JSON：{{"ok": true, "issues": []}} 或 {{"ok": false, "issues": ["..."]}}。不要输出其他内容。"""
    raw = get_llm().invoke(prompt).content
    try:
        data = json.loads(_strip_fences(raw))
        return bool(data.get("ok")), list(data.get("issues") or [])
    except Exception:
        return True, []  # 解析失败则放行（fail-open）


def _regenerate(answer: str, data_text: str, issues: list[str]) -> str:
    prompt = f"""你之前给出了一份回答，但经校验发现以下事实问题：
{chr(10).join(f'- {i}' for i in issues)}

请修正这些问题后重新输出完整回答。只修正事实错误，保持其他内容和结构不变；修正时只能用【工具数据】里的真实数值和对应关系。

【工具数据】
{data_text}

【原回答】
{answer}

【修正后的完整回答】"""
    return get_llm().invoke(prompt).content


def verify_with_verdict(answer: str, tool_outputs: list[tuple[str, str]]) -> tuple[str, bool, list[str]]:
    """校验最终回答，必要时重答一次；仍失败则标注 ⚠️。

    返回 (最终文本, 是否通过, 最终 issues)。评测用：暴露原始判定。
    """
    if not tool_outputs:
        return answer, True, []
    data_text = _format_tool_outputs(tool_outputs)

    ok, issues = _check(answer, data_text)
    if ok:
        logger.info("事实校验：通过")
        return answer, True, []

    logger.warning(f"事实校验发现问题，重答：{issues}")
    corrected = _regenerate(answer, data_text, issues)
    ok2, issues2 = _check(corrected, data_text)
    if ok2:
        logger.info("事实校验：重答后通过")
        return corrected, True, []
    logger.warning(f"事实校验：重答后仍有问题，标注：{issues2}")
    return corrected + "\n\n⚠️ 部分数据待核实：" + "；".join(issues2), False, issues2


def verify_and_correct(answer: str, tool_outputs: list[tuple[str, str]]) -> str:
    """校验最终回答（向后兼容薄包装：只返回文本）。"""
    text, _, _ = verify_with_verdict(answer, tool_outputs)
    return text
