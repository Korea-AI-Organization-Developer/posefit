"""플랭크 자세 검색기 (Retriever).

RAG 파이프라인의 '검색(R)' 단계.

# 역할
- 입력: 정규화 ViTPose 키포인트 프레임 스트림.
- 처리: 프레임마다 ChromaDB에 top-k 유사 자세 검색 → 거리 가중 다수결로 라벨 결정.
- 출력: 프레임별 라벨 시퀀스를 시간 구간(segment)으로 묶은 타임라인.

# 설계 결정
1. **거리 가중 투표 (distance-weighted vote)**
   ChromaDB가 반환하는 cosine distance d 를 가중치 w = 1 / (d + EPS) 로 환산해
   같은 라벨끼리 합산한다. 가장 가까운 이웃이 의미적으로 더 신뢰할 만하다는
   관찰에서 출발. 단순 vote count 보다 노이즈에 강하다.

2. **짧은 segment 흡수 (min_segment_frames)**
   1~수 프레임짜리 라벨 깜빡임(flicker)은 실제 자세 변화가 아니라 검색 노이즈로
   본다. 임계값(기본 5 프레임 = 30fps 기준 약 0.17초) 미만인 구간은 양옆 segment
   중 더 긴 쪽으로 흡수한다. 양옆 라벨이 같으면 그대로 병합되고, 다르면 LLM이
   읽기 좋은 굵은 segment 만 남는다.

3. **파일/이터러블 양쪽 입력 지원**
   - `retrieve_from_file(path)` — JSON 파일 한 개를 끝까지 처리하는 편의 함수.
   - `retrieve_frames(frames)` — `FrameSample` 이터러블을 받아 처리. 향후 API에서
     업로드된 데이터를 in-memory 로 흘려넣을 때 사용.

# 출력 자료구조
- `FramePrediction`  : 프레임 단위 결과(frame_id, timestamp_ms, label, confidence).
- `Segment`          : 연속된 동일 라벨 구간(start_ms, end_ms, label, frame_count,
                       avg_confidence).
- `RetrievalResult`  : 위 두 가지 + 전체 통계를 묶은 최종 산출물. 다음 단계인
                       프롬프트 빌더가 그대로 받아 사용한다.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .loader import FrameSample, iter_frames
from .store import get_collection
from .vectorize import frame_to_vector

# 거리(=cosine distance)가 0인 자기 자신 매치에서 0 나눔을 방지하기 위한 작은 값.
_EPS = 1e-6

# 기본 하이퍼파라미터. CLI/상위 호출자에서 override 가능.
DEFAULT_TOP_K = 5
DEFAULT_MIN_SEGMENT_FRAMES = 5  # 30fps 기준 약 0.17초 미만은 노이즈로 본다.


# ---------------------------------------------------------------------------
# 자료구조
# ---------------------------------------------------------------------------


@dataclass
class FramePrediction:
    """프레임 단위 검색 결과."""

    frame_id: int
    timestamp_ms: float
    label: str  # "correct" | "wrong"
    confidence: float  # 0~1, 거리 가중 다수 라벨의 점유율.


@dataclass
class Segment:
    """동일 라벨이 이어지는 시간 구간."""

    label: str
    start_ms: float
    end_ms: float
    frame_count: int
    avg_confidence: float


@dataclass
class RetrievalResult:
    """retriever 가 LLM 단계로 넘기는 패키지."""

    frame_predictions: list[FramePrediction]
    timeline: list[Segment]
    total_frames: int
    correct_ratio: float
    wrong_ratio: float
    video_file: str | None = None
    fps: float | None = None
    raw_neighbors: list[list[dict]] = field(default_factory=list)
    # raw_neighbors[i] = i번째 프레임에 대한 top-k 이웃 메타데이터. 디버깅·관찰용.


# ---------------------------------------------------------------------------
# 핵심 검색 로직
# ---------------------------------------------------------------------------


def _weighted_vote(labels: list[str], distances: list[float]) -> tuple[str, float]:
    """거리 가중 다수결.

    각 이웃의 가중치 = 1 / (distance + EPS) 로 두고 라벨별 합산.
    가장 큰 합을 갖는 라벨을 채택하고, 그 비율을 confidence 로 반환한다.

    Returns:
        (label, confidence) — confidence ∈ [0, 1].
    """
    bucket: dict[str, float] = defaultdict(float)
    for label, dist in zip(labels, distances):
        bucket[label] += 1.0 / (dist + _EPS)
    total = sum(bucket.values())
    label, weight = max(bucket.items(), key=lambda kv: kv[1])
    return label, weight / total if total > 0 else 0.0


def retrieve_frames(
    frames: Iterable[FrameSample],
    top_k: int = DEFAULT_TOP_K,
    collect_neighbors: bool = False,
) -> list[FramePrediction]:
    """프레임 이터러블 → 프레임 단위 예측 리스트.

    Args:
        frames: `loader.iter_frames` 또는 외부에서 흘려보내는 `FrameSample` 시퀀스.
        top_k:  ChromaDB top-k.
        collect_neighbors: True 이면 디버깅용으로 이웃 메타도 보관할 수 있게 한다.
                           (현재 함수는 prediction 리스트만 반환하므로 사용 X.
                            상위 retrieve() 에서 동일 옵션 처리.)
    """
    del collect_neighbors  # retrieve() 쪽에서 처리한다. 이 함수는 단순화 유지.
    collection = get_collection()
    predictions: list[FramePrediction] = []

    for sample in frames:
        vec = frame_to_vector(sample)
        result = collection.query(
            query_embeddings=[vec],
            n_results=top_k,
            include=["metadatas", "distances"],
        )
        metadatas = result["metadatas"][0] if result["metadatas"] else []
        distances = result["distances"][0] if result["distances"] else []
        if not metadatas:
            # 이웃이 없으면 라벨 결정 불가 → 해당 프레임은 스킵.
            continue

        labels = [m["label"] for m in metadatas]
        label, confidence = _weighted_vote(labels, distances)
        predictions.append(
            FramePrediction(
                frame_id=sample.frame_id,
                timestamp_ms=sample.timestamp_ms,
                label=label,
                confidence=confidence,
            )
        )
    return predictions


# ---------------------------------------------------------------------------
# 타임라인 구성
# ---------------------------------------------------------------------------


def _segments_from_predictions(predictions: list[FramePrediction]) -> list[Segment]:
    """연속된 같은 라벨을 한 segment 로 압축."""
    segments: list[Segment] = []
    if not predictions:
        return segments

    cur_label = predictions[0].label
    cur_start = predictions[0].timestamp_ms
    cur_end = predictions[0].timestamp_ms
    cur_conf_sum = predictions[0].confidence
    cur_count = 1

    for pred in predictions[1:]:
        if pred.label == cur_label:
            cur_end = pred.timestamp_ms
            cur_conf_sum += pred.confidence
            cur_count += 1
        else:
            segments.append(
                Segment(
                    label=cur_label,
                    start_ms=cur_start,
                    end_ms=cur_end,
                    frame_count=cur_count,
                    avg_confidence=cur_conf_sum / cur_count,
                )
            )
            cur_label = pred.label
            cur_start = pred.timestamp_ms
            cur_end = pred.timestamp_ms
            cur_conf_sum = pred.confidence
            cur_count = 1

    segments.append(
        Segment(
            label=cur_label,
            start_ms=cur_start,
            end_ms=cur_end,
            frame_count=cur_count,
            avg_confidence=cur_conf_sum / cur_count,
        )
    )
    return segments


def _absorb_short_segments(
    segments: list[Segment], min_frames: int
) -> list[Segment]:
    """짧은 segment 를 양옆으로 흡수.

    알고리즘:
      1. 짧은 segment 를 찾으면 양옆 중 더 긴 쪽의 라벨로 흡수.
      2. 흡수 후 인접 같은 라벨끼리는 다시 합친다(병합).
      3. 더 이상 짧은 segment 가 없을 때까지 반복.

    경계 처리:
      - 첫/마지막 segment 가 짧고 한쪽 이웃밖에 없으면 그 이웃으로 흡수.
      - 전체 segment 가 하나뿐이면 흡수 대상이 없으므로 그대로 둔다.
    """
    if not segments:
        return segments

    while True:
        # 짧은 segment 가 있는지 찾는다 (1개짜리 전체는 흡수 불가).
        if len(segments) == 1:
            return segments
        idx = next(
            (i for i, s in enumerate(segments) if s.frame_count < min_frames), -1
        )
        if idx == -1:
            return segments

        # 흡수 대상 결정.
        if idx == 0:
            target_label = segments[1].label
        elif idx == len(segments) - 1:
            target_label = segments[-2].label
        else:
            left, right = segments[idx - 1], segments[idx + 1]
            target_label = (
                left.label if left.frame_count >= right.frame_count else right.label
            )

        # 라벨만 바꾸고, 직후에 인접 동일 라벨 segment 를 병합.
        segments[idx] = Segment(
            label=target_label,
            start_ms=segments[idx].start_ms,
            end_ms=segments[idx].end_ms,
            frame_count=segments[idx].frame_count,
            avg_confidence=segments[idx].avg_confidence,
        )
        segments = _merge_adjacent_same_label(segments)


def _merge_adjacent_same_label(segments: list[Segment]) -> list[Segment]:
    """같은 라벨이 인접해 있으면 한 segment 로 합친다."""
    merged: list[Segment] = []
    for seg in segments:
        if merged and merged[-1].label == seg.label:
            prev = merged[-1]
            total = prev.frame_count + seg.frame_count
            merged[-1] = Segment(
                label=prev.label,
                start_ms=prev.start_ms,
                end_ms=seg.end_ms,
                frame_count=total,
                avg_confidence=(
                    prev.avg_confidence * prev.frame_count
                    + seg.avg_confidence * seg.frame_count
                )
                / total,
            )
        else:
            merged.append(seg)
    return merged


def build_timeline(
    predictions: list[FramePrediction],
    min_segment_frames: int = DEFAULT_MIN_SEGMENT_FRAMES,
) -> list[Segment]:
    """프레임 예측 → 평탄화된 타임라인.

    1) 같은 라벨끼리 연속 구간으로 묶고,
    2) 너무 짧은 구간은 양옆으로 흡수해 LLM 가독성을 높인다.
    """
    raw_segments = _segments_from_predictions(predictions)
    if min_segment_frames <= 1:
        return raw_segments
    return _absorb_short_segments(raw_segments, min_segment_frames)


# ---------------------------------------------------------------------------
# 통합 호출
# ---------------------------------------------------------------------------


def retrieve(
    frames: Iterable[FrameSample],
    top_k: int = DEFAULT_TOP_K,
    min_segment_frames: int = DEFAULT_MIN_SEGMENT_FRAMES,
    video_file: str | None = None,
    fps: float | None = None,
) -> RetrievalResult:
    """프레임 → 검색 → 타임라인 → 통계 묶음 한 번에.

    LLM 단계가 호출하는 최종 entry point.
    """
    predictions = retrieve_frames(frames, top_k=top_k)
    timeline = build_timeline(predictions, min_segment_frames=min_segment_frames)
    total = len(predictions)
    correct = sum(1 for p in predictions if p.label == "correct")
    return RetrievalResult(
        frame_predictions=predictions,
        timeline=timeline,
        total_frames=total,
        correct_ratio=(correct / total) if total else 0.0,
        wrong_ratio=((total - correct) / total) if total else 0.0,
        video_file=video_file,
        fps=fps,
    )


def retrieve_from_file(
    json_path: Path,
    top_k: int = DEFAULT_TOP_K,
    min_segment_frames: int = DEFAULT_MIN_SEGMENT_FRAMES,
) -> RetrievalResult:
    """JSON 파일 한 개를 처리하는 편의 함수.

    파일의 video_file / fps 메타도 같이 채워 LLM 단계에서 활용한다.
    """
    import json

    meta = json.loads(json_path.read_text(encoding="utf-8"))
    return retrieve(
        iter_frames(json_path),
        top_k=top_k,
        min_segment_frames=min_segment_frames,
        video_file=meta.get("video_file", json_path.name),
        fps=meta.get("fps"),
    )
