"""정규화 JSON 데이터셋을 ChromaDB에 적재한다.

사용법 (backend/ 에서):
    uv run python -m ai.rag.ingest
    uv run python -m ai.rag.ingest --reset
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .loader import iter_dataset
from .store import DEFAULT_COLLECTION, get_client, get_collection
from .vectorize import frame_to_vector

DEFAULT_DATA_ROOT = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "result"
    / "output"
    / "vitpose_normalized"
)

BATCH_SIZE = 512


def ingest(data_root: Path, reset: bool) -> int:
    client = get_client()
    if reset:
        try:
            client.delete_collection(DEFAULT_COLLECTION)
        except Exception:
            pass
    collection = get_collection(client)

    ids: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict] = []
    total = 0

    def flush() -> None:
        if not ids:
            return
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
        ids.clear()
        embeddings.clear()
        metadatas.clear()

    for sample in iter_dataset(data_root):
        ids.append(f"{sample.video_file}#{sample.frame_id}")
        embeddings.append(frame_to_vector(sample))
        metadatas.append(
            {
                "video_file": sample.video_file,
                "label": sample.label,
                "frame_id": sample.frame_id,
                "timestamp_ms": sample.timestamp_ms,
            }
        )
        total += 1
        if len(ids) >= BATCH_SIZE:
            flush()
    flush()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="플랭크 정규화 JSON → ChromaDB 적재")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--reset", action="store_true", help="기존 컬렉션을 비우고 새로 적재")
    args = parser.parse_args()

    print(f"[ingest] data_root = {args.data_root}")
    total = ingest(args.data_root, reset=args.reset)
    print(f"[ingest] 적재 완료: {total} 프레임")


if __name__ == "__main__":
    main()
