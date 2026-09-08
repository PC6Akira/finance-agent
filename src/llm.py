"""LLM 构造：从 settings 创建 DeepSeek 对话模型。"""
from langchain_deepseek import ChatDeepSeek

from src.config import settings


def get_llm() -> ChatDeepSeek:
    return ChatDeepSeek(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key,
        temperature=settings.llm_temperature,
    )
