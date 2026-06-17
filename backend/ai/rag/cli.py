"""코칭 조회 CLI — 분석 결과 JSON을 받아 오류별 코칭 코멘트를 출력한다.

사용법 (backend/ 에서):
    uv run python -m ai.rag.cli ../rag_docs/group.json.txt
    uv run python -m ai.rag.cli ../rag_docs/group.json.txt --no-llm   # 검색 결과만(무비용)
"""

from __future__ import annotations

import argparse
import sys

from ai.rag.pipeline import coach


def main() -> None:
    parser = argparse.ArgumentParser(description="PoseFit RAG 코칭 조회")
    parser.add_argument("input", help="analysis_result JSON 경로")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Gemini 합성을 건너뛰고 검색된 코칭문구 원문만 출력",
    )
    args = parser.parse_args()

    results = coach(args.input, synthesize=not args.no_llm)

    if not results:
        print("감지된 오류가 없습니다 (errors 비어 있음).")
        return

    for r in results:
        print("=" * 60)
        print(f"오류: {r.error_name} [{r.error_code}] (심각도: {r.severity})")
        print(f"검색된 문서: {', '.join(r.retrieved_doc_ids)}")
        print("-" * 60)
        print(r.comment)
        print()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        sys.exit(1)
