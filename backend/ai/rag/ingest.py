"""인덱스 빌드 CLI — 코칭 문서를 임베딩해 Chroma에 저장한다.

사용법 (backend/ 에서):
    uv run python -m ai.rag.ingest
"""

from __future__ import annotations

from ai.rag.config import settings
from ai.rag.vectorstore import build_index


def main() -> None:
    print(f"코칭 문서 인덱싱 시작 — 임베딩 모델: {settings.bge_model}")
    count = build_index()
    print(f"완료: {count}개 청크를 '{settings.collection_name}' 컬렉션에 저장")
    print(f"저장 위치: {settings.persist_dir}")


if __name__ == "__main__":
    main()
