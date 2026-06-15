"""ChromaDB로 플랭크 자세 프레임 단위 분류.

각 프레임에 top-k 검색 → 다수결로 correct / wrong 결정.
연속된 같은 라벨 구간을 합쳐 (start_ms, end_ms, label) 타임라인을 만든다.

사용법 (backend/ 에서):
    uv run python -m ai.rag.query <query.json>
    uv run python -m ai.rag.query <query.json> --top-k 7
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .loader import iter_frames
from .store import get_collection
from .vectorize import frame_to_vector


@dataclass
class FramePrediction:
    frame_id: int
    timestamp_ms: float
    label: str
    confidence: float  # 0~1, 다수 라벨 비율


@dataclass
class Segment:
    label: str
    start_ms: float
    end_ms: float
    frame_count: int


def classify_frames(json_path: Path, top_k: int = 5) -> list[FramePrediction]:
    collection = get_collection()
    predictions: list[FramePrediction] = []

    for sample in iter_frames(json_path):
        vec = frame_to_vector(sample)
        result = collection.query(
            query_embeddings=[vec],
            n_results=top_k,
            include=["metadatas"],
        )
        metadatas = result["metadatas"][0] if result["metadatas"] else []
        if not metadatas:
            continue
        labels = [m["label"] for m in metadatas]
        counts = Counter(labels)
        label, count = counts.most_common(1)[0]
        predictions.append(
            FramePrediction(
                frame_id=sample.frame_id,
                timestamp_ms=sample.timestamp_ms,
                label=label,
                confidence=count / len(labels),
            )
        )
    return predictions


def to_timeline(predictions: list[FramePrediction]) -> list[Segment]:
    segments: list[Segment] = []
    if not predictions:
        return segments
    cur = Segment(
        label=predictions[0].label,
        start_ms=predictions[0].timestamp_ms,
        end_ms=predictions[0].timestamp_ms,
        frame_count=1,
    )
    for pred in predictions[1:]:
        if pred.label == cur.label:
            cur.end_ms = pred.timestamp_ms
            cur.frame_count += 1
        else:
            segments.append(cur)
            cur = Segment(
                label=pred.label,
                start_ms=pred.timestamp_ms,
                end_ms=pred.timestamp_ms,
                frame_count=1,
            )
    segments.append(cur)
    return segments


def main() -> None:
    parser = argparse.ArgumentParser(description="플랭크 JSON 프레임 분류 + 타임라인 출력")
    parser.add_argument("query_json", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    predictions = classify_frames(args.query_json, top_k=args.top_k)
    if not predictions:
        print("분류 가능한 프레임이 없습니다.")
        return

    total = len(predictions)
    correct = sum(1 for p in predictions if p.label == "correct")
    wrong = total - correct
    print(f"전체 프레임: {total}")
    print(f"  correct: {correct} ({correct / total:.1%})")
    print(f"  wrong  : {wrong} ({wrong / total:.1%})")
    print()
    print("타임라인 (segment):")
    for seg in to_timeline(predictions):
        print(
            f"  [{seg.start_ms / 1000:7.2f}s ~ {seg.end_ms / 1000:7.2f}s] "
            f"{seg.label:7s} ({seg.frame_count} frames)"
        )


if __name__ == "__main__":
    main()
