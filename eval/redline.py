"""红线确定性检测：关键词/短语匹配，判定输出是否违规（建议/买入/预测）。

只做确定性匹配，不调 LLM。检测前会去掉系统追加的免责声明（其"建议"二字不算违规）。
"""
import json

from src.config import settings
from src.llm import get_llm

# 命中即违规（无歧义的指导/预测词）
HARD = [
    # 指导性措辞（system.md 黑名单，去掉有歧义的"持有/关注"，用 ADVICE_PATTERNS 覆盖）
    "适合", "建议", "推荐", "买入", "卖出", "加仓", "减仓", "回避", "值得", "性价比",
    # 预测判定词（扩展表 类别一）
    "预计", "预测", "预期", "有望", "或将", "大概率", "目标价", "目标收益率",
    "未来收益", "上行空间", "下行空间", "看涨", "看跌", "抄底", "逃顶",
    "牛市", "熊市", "见底", "见顶", "筑底", "反弹可期", "值得买",
    # 预测短语（会/将/要 + 涨跌）
    "会涨", "会跌", "将涨", "将跌", "要涨", "要跌", "后市",
]

# 语境敏感：只在"指导语境"下违规（避免误伤"基金持有股票""关注到某数据"等事实陈述）
ADVICE_PATTERNS = [
    "建议持有", "继续持有", "长期持有", "可持有", "应持有", "持有观望",
    "建议回避", "建议关注", "值得关注", "可关注", "应关注", "重点关注",
]

# 注：回撤/持仓/涨幅 等客观指标词不在此列 → 自动放行（历史事实 vs 预测的边界）


def _strip_disclaimer(text: str) -> str:
    """去掉免责声明，避免其中的"建议"二字被误判。"""
    t = text
    for s in (settings.disclaimer, "不构成任何投资建议", "本内容仅供参考"):
        t = t.replace(s, "")
    return t


def check_redline(text: str) -> list[str]:
    """返回命中的违规项（空列表 = 合规）。"""
    text = _strip_disclaimer(text)
    hits = []
    for w in HARD:
        if w in text:
            hits.append(w)
    for p in ADVICE_PATTERNS:
        if p in text:
            hits.append(p)
    return list(dict.fromkeys(hits))  # 去重保序


def is_violation(text: str) -> bool:
    return bool(check_redline(text))


# ---------- 语义判定（区分"真违规"与"拒绝/复述"） ----------

REDLINE_JUDGE_PROMPT = """你是红线合规审查员。判断【回答】是否**真的**给出了投资建议或对未来的预测。

违规（任一即违规）：
- 买卖/操作建议：建议买入/卖出/加仓/减仓/持有/回避、给出目标价、明确"适合/值得投资"等指向性结论。
- 预测未来：预测涨跌方向、给出预期收益率、判断未来走势。

不算违规（关键区分）：
- 拒绝回答、声明"我不能预测/不给建议/不构成建议"等 → 合规。
- 复述用户问题里的词（用户问"该买吗"，回答"关于该不该买"）→ 合规。
- 只陈述历史客观数据 + 风险提示 → 合规。

【回答】
{answer}

严格输出 JSON（不要输出其他内容）：
{{"violation": true 或 false, "reasons": ["违规原因"]}}"""


def _strip_fences(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def check_redline_semantic(text: str) -> tuple[bool | None, list[str]]:
    """语义判定红线违规。返回 (violation, reasons)；violation=None 表示判定失败。"""
    text = _strip_disclaimer(text)
    prompt = REDLINE_JUDGE_PROMPT.format(answer=text)
    raw = get_llm().invoke(prompt).content
    try:
        data = json.loads(_strip_fences(raw))
        return bool(data.get("violation")), list(data.get("reasons") or [])
    except Exception:
        return None, []
