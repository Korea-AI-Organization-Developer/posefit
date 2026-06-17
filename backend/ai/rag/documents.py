"""코칭 지식 JSON → LangChain Document 변환.

rag_docs 안의 코칭 문서는 세 가지 스키마가 섞여 있다:
  1) 루트 plank/*.json      — 오류별 coaching_case (doc_id, issue_key, 오류설명, 원인가능성, 코칭문구 …)
  2) plank/v2/*.json        — 영상×window별 오류코칭사례 (문서ID, 주오류, 오류명, 대표관찰값 …)
  3) 자세기준(exam.json,     — 정상 자세 reference (문서ID, 자세설명, 코칭문구, 라벨=정상 …)
     v2/correct/*.json)

세 스키마를 한국어 키 기준으로 흡수해, 검색 친화적 본문(page_content) 하나와
구조화된 metadata를 가진 Document로 만든다. 본문은 문서당 1개를 기본 단위로 하되,
chunk_size를 넘으면 RecursiveCharacterTextSplitter로 보조 분할한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai.rag.config import settings


def _as_lines(value: Any) -> list[str]:
    """문자열 또는 문자열 리스트를 줄 목록으로 정규화."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def _flatten_observations(obs: dict[str, Any]) -> str:
    """대표관찰값/관찰사례 dict를 'feature: 평균 .., 최대 ..' 형태의 한 줄들로 직렬화."""
    lines: list[str] = []
    for feature, stat in obs.items():
        if isinstance(stat, dict):
            parts = [f"{k} {v}" for k, v in stat.items()]
            lines.append(f"- {feature}: {', '.join(parts)}")
        else:
            lines.append(f"- {feature}: {stat}")
    return "\n".join(lines)


def _doc_id(raw: dict[str, Any], path: Path) -> str:
    return str(raw.get("doc_id") or raw.get("문서ID") or path.stem)


def _serialize(raw: dict[str, Any], path: Path) -> tuple[str, dict[str, Any]]:
    """원본 JSON → (page_content, metadata).

    page_content는 임베딩 검색용 한국어 텍스트. 여러 스키마의 동일 의미 필드를
    or 체인으로 흡수한다.
    """
    doc_id = _doc_id(raw, path)
    issue_key = raw.get("issue_key") or raw.get("주오류") or ""
    label = raw.get("라벨", "")
    view = raw.get("촬영방향", "")
    exercise = raw.get("운동명", "플랭크")
    issue_name = raw.get("오류명", "")

    # 관찰값: 대표관찰값(v2) 또는 관찰사례(루트)
    observations = raw.get("대표관찰값") or raw.get("관찰사례") or {}

    sections: list[str] = []
    sections.append(f"운동: {exercise} / 촬영방향: {view} / 라벨: {label}")
    if issue_name or issue_key:
        sections.append(f"오류: {issue_name} ({issue_key})".strip())

    # 설명: 오류설명 / 자세설명 / 관찰메모
    for key in ("오류설명", "자세설명", "관찰메모"):
        for line in _as_lines(raw.get(key)):
            sections.append(line)

    causes = _as_lines(raw.get("원인가능성"))
    if causes:
        sections.append("원인 가능성:\n" + "\n".join(f"- {c}" for c in causes))

    coaching = _as_lines(raw.get("코칭문구"))
    if coaching:
        sections.append("코칭문구:\n" + "\n".join(f"- {c}" for c in coaching))

    caution = _as_lines(raw.get("주의사항"))
    if caution:
        sections.append("주의사항: " + " ".join(caution))

    if isinstance(observations, dict) and observations:
        sections.append("관찰값:\n" + _flatten_observations(observations))

    keywords = _as_lines(raw.get("검색키워드"))
    if keywords:
        sections.append("검색키워드: " + ", ".join(keywords))

    page_content = "\n".join(s for s in sections if s).strip()

    metadata: dict[str, Any] = {
        "doc_id": doc_id,
        "issue_key": issue_key,
        "label": label,
        "view": view,
        "source": str(path.relative_to(settings.rag_docs_dir)),
        # Chroma metadata는 스칼라만 허용 → 코칭문구 원문은 join해서 저장
        "coaching": " || ".join(coaching),
    }
    return page_content, metadata


def load_coaching_docs() -> list[Document]:
    """설정된 glob에 해당하는 코칭 JSON을 모두 읽어 Document 리스트로 반환."""
    paths: list[Path] = []
    seen: set[Path] = set()
    for pattern in settings.source_globs:
        for p in sorted(settings.rag_docs_dir.glob(pattern)):
            if p.is_file() and p not in seen:
                seen.add(p)
                paths.append(p)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documents: list[Document] = []
    for path in paths:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[skip] {path.name}: {exc}")
            continue

        page_content, metadata = _serialize(raw, path)
        if not page_content:
            continue

        chunks = splitter.split_text(page_content)
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            meta = dict(metadata)
            if total > 1:
                meta["chunk"] = i
            documents.append(Document(page_content=chunk, metadata=meta))

    return documents
