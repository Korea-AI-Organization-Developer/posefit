"""RAG 설정 — 경로, 모델명, 검색 파라미터.

환경변수로 덮어쓸 수 있다 (`backend/.env` 또는 셸 export). 필드명은 대소문자 무시로
같은 이름의 환경변수에 매핑된다:
    GOOGLE_API_KEY   — Gemini API 키 (합성 단계에 필요)
    GEMINI_MODEL     — 생성 모델명 (기본 gemini-2.0-flash)
    BGE_MODEL        — 임베딩 모델명 (기본 BAAI/bge-m3)
    TOP_K            — 오류당 검색 문서 수 (기본 4)
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ai/rag/config.py -> backend/ -> posefit/
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent


class RagSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- 경로 ---
    rag_docs_dir: Path = _REPO_ROOT / "rag_docs"
    persist_dir: Path = _BACKEND_DIR / "ai" / "rag" / ".chroma"
    collection_name: str = "posefit_coaching"

    # 지식 베이스 소스 glob (rag_docs_dir 기준 상대경로).
    # 루트 오류 코칭사례 + v2 window별 사례 + 정상 자세 기준(exam.json / v2/correct).
    # 원천 feature(windows/)와 중복본(v2 copy/)은 제외.
    source_globs: tuple[str, ...] = (
        "plank/*.json",
        "plank/v2/*.json",
        "plank/v2/correct/*.json",
        "exam.json",
    )

    # 확장 RAG 코퍼스(JSONL). v3는 오류코드 7종 × 관점 14종 = 98개의 사전 직렬화
    # 코칭 문서로, 한 줄(line) = 한 문서다. 각 줄은 임베딩용 본문(document)·메타데이터·
    # 원본(raw_json)을 담는다. 이미 관점별로 의미 단위가 나뉘어 있어 재분할하지 않는다.
    jsonl_globs: tuple[str, ...] = ("plank/v3/*.jsonl",)

    # --- 모델 ---
    bge_model: str = Field(default="BAAI/bge-m3", alias="BGE_MODEL")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")

    # --- 청킹 ---
    chunk_size: int = 800
    chunk_overlap: int = 100

    # --- 검색 ---
    top_k: int = Field(default=4, alias="TOP_K")


settings = RagSettings()
