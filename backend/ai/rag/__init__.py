"""PoseFit RAG 코칭 패키지.

분류된 운동 자세 오류(analysis_result)를 입력받아, 코칭 지식 문서를 벡터 검색하고
Gemini Flash로 사용자 관측값에 맞춘 코칭 코멘트를 생성한다.

공개 API:
    build_index() — 코칭 문서를 임베딩해 Chroma 인덱스 구축
    coach(input_path) — 입력 분석 결과에 대한 코칭 코멘트 생성
"""

from ai.rag.pipeline import coach
from ai.rag.vectorstore import build_index

__all__ = ["build_index", "coach"]
