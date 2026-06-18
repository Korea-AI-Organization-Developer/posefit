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
from ai.rag.query import issue_key_from_error_code


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


_VIEW_KO = {"side": "측면", "front": "정면"}


def _jsonl_metadata(record: dict[str, Any], path: Path) -> dict[str, Any]:
    """v3 JSONL 한 줄의 metadata/raw_json → 기존 인덱스 스키마 메타데이터.

    조회(query)·파이프라인이 기대하는 키(doc_id / issue_key / label / view /
    source / coaching)로 변환한다. 특히 issue_key는 query 쪽과 동일한 규칙으로
    error_code에서 뽑아야 `where={"issue_key": ...}` 필터가 일치한다.
    """
    meta = record.get("metadata", {}) or {}
    raw = record.get("raw_json", {}) or {}

    doc_id = str(record.get("id") or meta.get("source_base_doc") or path.stem)
    error_code = str(meta.get("error_code") or raw.get("오류코드") or "")
    issue_key = issue_key_from_error_code(error_code) if error_code else ""
    camera_view = str(meta.get("camera_view") or "")
    view = _VIEW_KO.get(camera_view, raw.get("촬영방향", camera_view))

    # --no-llm 모드가 쓰는 코칭문구 원문 (raw_json의 코칭문구 → " || " 결합)
    coaching = " || ".join(_as_lines(raw.get("코칭문구")))

    return {
        "doc_id": doc_id,
        "issue_key": issue_key,
        "label": "오류",  # v3 코퍼스는 오류별 코칭 확장 문서다
        "view": view,
        "source": f"{path.relative_to(settings.rag_docs_dir)}#{doc_id}",
        "coaching": coaching,
        # v3 전용 부가 메타 (검색 필터/디버깅용)
        "error_code": error_code,
        "variant": str(meta.get("variant", "")),
        "rag_version": str(meta.get("rag_version", "")),
    }


def load_jsonl_docs() -> list[Document]:
    """jsonl_globs에 해당하는 확장 RAG 코퍼스(JSONL)를 Document 리스트로 반환.

    각 줄의 `document`는 이미 임베딩 친화적으로 직렬화돼 있고 관점 단위로 나뉘어
    있으므로 재분할(splitter)하지 않고 한 줄 = 한 Document로 적재한다.
    """
    documents: list[Document] = []
    for pattern in settings.jsonl_globs:
        for path in sorted(settings.rag_docs_dir.glob(pattern)):
            if not path.is_file():
                continue
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"[skip] {path.name}:{lineno}: {exc}")
                    continue
                content = (record.get("document") or "").strip()
                if not content:
                    continue
                documents.append(
                    Document(page_content=content, metadata=_jsonl_metadata(record, path))
                )
    return documents


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

    # 확장 RAG 코퍼스(JSONL)를 같은 컬렉션에 합친다.
    documents.extend(load_jsonl_docs())

    return documents
