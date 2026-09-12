"""LLM-as-judge：核对回答里的事实是否与工具数据一致，判"含错"。

提示词比 verifier 更强（清单式、要求引原话、判名次错），用于端到端层算含错率/净收益。
"""
import json

from src.llm import get_llm

JUDGE_PROMPT = """你是严格的事实核查员。核对【回答】里的每个事实性陈述（具体数值、基金代码/名称、日期、指标名、名次），判断能否在【工具数据】里找到一致支撑。

判据（逐条）：
- 编造：数值/事实在工具数据里完全不存在 → 记错误。
- 错配：数值存在，但对应的基金、指标、名次对不上 → 记错误。
- 名次错：把第二大说成第一大等 → 记错误。
- 允许：合理四舍五入/约等（2.908 说成约 2.91）；"约/接近/不足/超过"只要方向正确不算错。
- 只判事实对错，不判推理、解读、结论是否妥当，不判措辞是否合规。

【工具数据】
{data_text}

【回答】
{answer}

严格输出 JSON（不要输出其他内容）：
{{"has_error": true 或 false, "errors": [{{"claim": "回答原话", "reason": "错在哪"}}]}}"""


def _strip_fences(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def judge(answer: str, data_text: str) -> tuple[bool | None, list[str]]:
    """返回 (has_error, errors)。has_error=None 表示判定失败（待人工复核）。"""
    if not data_text.strip():
        return None, []  # 无工具数据，无法核对事实
    prompt = JUDGE_PROMPT.format(data_text=data_text, answer=answer)
    raw = get_llm().invoke(prompt).content
    try:
        data = json.loads(_strip_fences(raw))
        return bool(data.get("has_error")), [e.get("reason", "") for e in (data.get("errors") or [])]
    except Exception:
        return None, []  # 解析失败 → 待人工复核
