"""RAG 파이프라인 — 입력 오류를 검색하고 Gemini Flash로 코칭 코멘트를 생성한다."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from ai.rag.config import settings
from ai.rag.query import ErrorQuery, parse_analysis_result
from ai.rag.vectorstore import search

_SYSTEM_PROMPT = (
    "당신은 플랭크 운동 자세를 교정해 주는 전문 코치입니다. "
    "사용자에게 감지된 자세 오류와 그 관측값, 그리고 참고용 코칭 지식이 주어집니다. "
    "참고 지식에 근거해 사용자의 관측값을 반영한 코칭을 작성하세요.\n"
    "규칙:\n"
    "- 참고 지식에 없는 사실이나 수치를 지어내지 마세요.\n"
    "- 한국어로, 2~3문장의 실천 가능한 코칭 + 필요한 경우 한 줄 주의사항으로 끝내세요.\n"
    "- 전문 용어보다 사용자가 바로 따라 할 수 있는 큐(cue) 중심으로 설명하세요."
)


@dataclass
class Coaching:
    error_code: str
    error_name: str
    severity: str
    comment: str
    retrieved_doc_ids: list[str] = field(default_factory=list)


def _format_context(docs: list[Document]) -> str:
    blocks = []
    for d in docs:
        blocks.append(
            f"[문서 {d.metadata.get('doc_id')} | issue={d.metadata.get('issue_key')} "
            f"| label={d.metadata.get('label')}]\n{d.page_content}"
        )
    return "\n\n".join(blocks)


def _build_prompt(eq: ErrorQuery, docs: list[Document]) -> str:
    observed = "\n".join(
        f"- {f}: 관측 {v}" + (f" (기준 {eq.threshold.get(f)})" if f in eq.threshold else "")
        for f, v in eq.observed.items()
    )
    return (
        f"## 감지된 오류\n{eq.error_name} ({eq.issue_key}), 심각도: {eq.severity}\n\n"
        f"## 관측값\n{observed or '(제공된 수치 없음)'}\n\n"
        f"## 참고 코칭 지식\n{_format_context(docs)}\n\n"
        "위 오류에 대한 코칭 코멘트를 작성하세요."
    )


def _retrieve(eq: ErrorQuery) -> list[Document]:
    """issue_key 메타데이터 필터로 우선 검색하고, 부족하면 전체에서 시맨틱 보강."""
    docs: list[Document] = []
    if eq.issue_key:
        docs = search(eq.to_text(), where={"issue_key": eq.issue_key})
    if len(docs) < settings.top_k:
        extra = search(eq.to_text())
        seen = {(d.metadata.get("doc_id"), d.metadata.get("chunk")) for d in docs}
        for d in extra:
            key = (d.metadata.get("doc_id"), d.metadata.get("chunk"))
            if key not in seen:
                docs.append(d)
                seen.add(key)
            if len(docs) >= settings.top_k:
                break
    return docs[: settings.top_k]


def _get_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY가 설정되지 않았습니다. backend/.env에 추가하거나 "
            "coach(..., synthesize=False)로 검색 결과만 확인하세요."
        )
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.3,
    )


def coach(input_path: str | Path, synthesize: bool = True) -> list[Coaching]:
    """입력 분석 결과 파일에 대한 오류별 코칭 코멘트를 생성한다.

    Args:
        input_path: analysis_result JSON 경로 (예: rag_docs/group.json.txt).
        synthesize: True면 Gemini로 합성, False면 검색된 코칭문구 원문을 반환(무비용).
    """
    queries = parse_analysis_result(input_path)
    llm = _get_llm() if synthesize else None

    results: list[Coaching] = []
    for eq in queries:
        docs = _retrieve(eq)
        doc_ids = [d.metadata.get("doc_id", "") for d in docs]

        if synthesize and llm is not None:
            messages = [
                ("system", _SYSTEM_PROMPT),
                ("human", _build_prompt(eq, docs)),
            ]
            comment = llm.invoke(messages).content
        else:
            # 검색된 문서의 코칭문구 원문을 합쳐 반환
            lines: list[str] = []
            for d in docs:
                raw = d.metadata.get("coaching", "")
                lines.extend(p for p in raw.split(" || ") if p)
            comment = "\n".join(f"- {ln}" for ln in dict.fromkeys(lines)) or "(검색 결과 없음)"

        results.append(
            Coaching(
                error_code=eq.error_code,
                error_name=eq.error_name,
                severity=eq.severity,
                comment=str(comment).strip(),
                retrieved_doc_ids=doc_ids,
            )
        )
    return results
