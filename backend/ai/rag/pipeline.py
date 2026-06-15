"""플랭크 RAG 통합 파이프라인 CLI.

# 흐름
    query JSON
       │
       ▼  loader.iter_frames
    프레임 스트림
       │
       ▼  retriever.retrieve  (ChromaDB top-k + 거리가중 투표 + segment 흡수)
    RetrievalResult (프레임 예측 + 타임라인 + 통계)
       │
       ▼  prompt.build_prompt
    GeminiPrompt (시스템 + 사용자)
       │
       ▼  llm.call_gemini      (Gemini 2.5 Flash)
    LlmResponse (한국어 마크다운 코멘트)

사용법 (backend/ 에서):
    uv run python -m ai.rag.pipeline <query.json>
    uv run python -m ai.rag.pipeline <query.json> --top-k 7 --min-segment 3 \
        --model gemini-2.5-pro

옵션:
    --skip-llm   검색·프롬프트까지만 수행하고 LLM 호출은 생략(키 없을 때 유용).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .llm import DEFAULT_MODEL, MissingApiKeyError, call_gemini


def _force_utf8_stdout() -> None:
    """Windows cp949 콘솔에서도 한국어·em-dash 가 깨지지 않게 stdout 을 UTF-8 로 재설정."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
from .prompt import build_prompt
from .retriever import (
    DEFAULT_MIN_SEGMENT_FRAMES,
    DEFAULT_TOP_K,
    retrieve_from_file,
)


def _print_section(title: str) -> None:
    print()
    print(f"===== {title} =====")


def main() -> None:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(description="플랭크 RAG 통합 파이프라인")
    parser.add_argument("query_json", type=Path)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--min-segment",
        type=int,
        default=DEFAULT_MIN_SEGMENT_FRAMES,
        help="이 프레임 수 미만 segment 는 양옆으로 흡수",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini 모델명")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="LLM 호출 없이 검색·프롬프트까지만 출력",
    )
    args = parser.parse_args()

    # 1) 검색 + 타임라인
    result = retrieve_from_file(
        args.query_json,
        top_k=args.top_k,
        min_segment_frames=args.min_segment,
    )

    _print_section("검색 결과")
    print(f"영상: {result.video_file}  (fps={result.fps})")
    print(f"전체 프레임: {result.total_frames}")
    print(
        f"  correct: {result.correct_ratio:.1%}   "
        f"wrong: {result.wrong_ratio:.1%}"
    )
    print()
    print("타임라인:")
    for seg in result.timeline:
        print(
            f"  [{seg.start_ms / 1000:7.2f}s ~ {seg.end_ms / 1000:7.2f}s] "
            f"{seg.label:7s}  conf={seg.avg_confidence:.2f}  "
            f"({seg.frame_count} frames)"
        )

    # 2) 프롬프트 빌드
    prompt = build_prompt(result)
    _print_section("Gemini 사용자 프롬프트")
    print(prompt.user)

    if args.skip_llm:
        _print_section("LLM 호출 생략 (--skip-llm)")
        return

    # 3) LLM 호출
    try:
        response = call_gemini(prompt, model=args.model)
    except MissingApiKeyError as e:
        _print_section("LLM 호출 실패")
        print(str(e))
        return

    _print_section(f"Gemini 응답  (model={response.model}, {response.elapsed_s:.2f}s)")
    print(response.text)


if __name__ == "__main__":
    main()
