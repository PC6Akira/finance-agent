"""输出合规：统一注入免责声明。"""
from src.config import settings


def finalize(text: str) -> str:
    """在输出末尾追加免责声明；若已含免责声明（含 LLM 自行添加的变体）则不重复。"""
    disclaimer = settings.disclaimer
    if not text:
        return disclaimer
    if "不构成" in text:  # 已含「不构成…投资建议」类表述
        return text
    return text.rstrip() + "\n\n" + disclaimer
