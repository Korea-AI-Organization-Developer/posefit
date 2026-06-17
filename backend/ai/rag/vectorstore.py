"""Chroma 벡터스토어 — BGE 임베딩으로 코칭 문서 인덱스 구축/로드."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from ai.rag.config import settings
from ai.rag.documents import load_coaching_docs


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """BGE 임베딩 모델 (프로세스당 1회 로드)."""
    return HuggingFaceEmbeddings(
        model_name=settings.bge_model,
        encode_kwargs={"normalize_embeddings": True},
    )


def build_index() -> int:
    """코칭 문서를 임베딩해 Chroma에 영구 저장한다. 기존 컬렉션은 재생성한다.

    Returns:
        인덱싱된 청크 수.
    """
    documents = load_coaching_docs()
    if not documents:
        raise RuntimeError(
            f"코칭 문서를 찾지 못했습니다. source_globs와 {settings.rag_docs_dir}를 확인하세요."
        )

    settings.persist_dir.mkdir(parents=True, exist_ok=True)

    # 재인덱싱 시 중복 방지를 위해 기존 컬렉션을 비우고 새로 만든다.
    store = Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.persist_dir),
    )
    try:
        store.delete_collection()
    except Exception:  # noqa: BLE001 — 컬렉션이 없으면 무시
        pass

    store = Chroma.from_documents(
        documents=documents,
        embedding=get_embeddings(),
        collection_name=settings.collection_name,
        persist_directory=str(settings.persist_dir),
    )
    return len(documents)


@lru_cache(maxsize=1)
def get_store() -> Chroma:
    """기존 인덱스를 로드한다 (없으면 비어 있는 컬렉션)."""
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.persist_dir),
    )


def search(query: str, k: int | None = None, where: dict[str, Any] | None = None):
    """유사도 검색. where는 Chroma 메타데이터 필터 (예: {'issue_key': 'hip_sag'})."""
    store = get_store()
    return store.similarity_search(query, k=k or settings.top_k, filter=where)
