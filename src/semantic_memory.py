"""语义记忆：Chroma 向量库，存访谈 / 舆情 / 公告，支持语义检索。"""
from langchain_chroma import Chroma

from src.config import settings
from src.embeddings import get_embeddings

_COLLECTION = "finance_memory"
_store: Chroma | None = None


def _get_store() -> Chroma:
    global _store
    if _store is None:
        _store = Chroma(
            collection_name=_COLLECTION,
            embedding_function=get_embeddings(),
            persist_directory=str(settings.chroma_path),
        )
    return _store


def add_texts(texts: list[str], metadatas: list[dict] | None = None, ids: list[str] | None = None) -> None:
    """写入文本（含元数据 / ID）。"""
    _get_store().add_texts(texts, metadatas=metadatas, ids=ids)


def search(query: str, k: int = 5) -> list[dict]:
    """语义检索，返回 [{text, meta}]。"""
    docs = _get_store().similarity_search(query, k=k)
    return [{"text": d.page_content, "meta": d.metadata} for d in docs]
