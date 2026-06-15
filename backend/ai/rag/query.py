"""검색 결과 확인용 CLI.

`retriever.py` 의 로직을 호출해 프레임별 라벨과 segment 타임라인을 콘솔에 출력한다.
LLM 코멘트 생성 없이 검색 단계만 단독 점검할 때 사용한다.

사용법 (backend/ 에서):
    uv run python -m ai.rag.query <query.json>
    uv run python -m ai.rag.query <query.json> --top-k 7 --min-segment 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .retriever import (
    DEFAULT_MIN_SEGMENT_FRAMES,
    DEFAULT_TOP_K,
    retrieve_from_file,
)


def main() -> None:
    # Windows cp949 콘솔에서도 한국어가 깨지지 않게 stdout 을 UTF-8 로 재설정.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="플랭크 자세 검색 단독 실행 — 타임라인까지만 출력"
    )
    parser.add_argument("query_json", type=Path)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--min-segment",
        type=int,
        default=DEFAULT_MIN_SEGMENT_FRAMES,
        help="이 프레임 수 미만의 segment 는 양옆으로 흡수",
    )
    args = parser.parse_args()

    result = retrieve_from_file(
        args.query_json,
        top_k=args.top_k,
        min_segment_frames=args.min_segment,
    )

    if result.total_frames == 0:
        print("분류 가능한 프레임이 없습니다.")
        return

    print(f"영상: {result.video_file}  (fps={result.fps})")
    print(f"전체 프레임: {result.total_frames}")
    print(f"  correct: {result.correct_ratio:.1%}")
    print(f"  wrong  : {result.wrong_ratio:.1%}")
    print()
    print("타임라인 (segment):")
    for seg in result.timeline:
        print(
            f"  [{seg.start_ms / 1000:7.2f}s ~ {seg.end_ms / 1000:7.2f}s] "
            f"{seg.label:7s}  conf={seg.avg_confidence:.2f}  "
            f"({seg.frame_count} frames)"
        )


if __name__ == "__main__":
    main()
