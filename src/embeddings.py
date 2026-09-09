"""Embedding：千问 DashScope（text-embedding-v3，1024 维）。"""
from langchain_community.embeddings import DashScopeEmbeddings

from src.config import settings


def get_embeddings() -> DashScopeEmbeddings:
    return DashScopeEmbeddings(
        model=settings.embedding_model,
        dashscope_api_key=settings.qwen_api_key,
    )
