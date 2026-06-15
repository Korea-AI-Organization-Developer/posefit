"""ChromaDB persistent 클라이언트 래퍼."""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.config import Settings

DEFAULT_DB_DIR = Path(__file__).resolve().parents[3] / "data" / "vectordb" / "chroma"
DEFAULT_COLLECTION = "plank_frames"


def get_client(db_dir: Path = DEFAULT_DB_DIR) -> chromadb.api.ClientAPI:
    db_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(db_dir),
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(
    client: chromadb.api.ClientAPI | None = None,
    name: str = DEFAULT_COLLECTION,
):
    client = client or get_client()
    # 코사인 거리 사용 — 자세 모양 유사도 비교에 직관적.
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
