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
    "당신은 플랭크 자세를 교정해 주는 따뜻하고 전문적인 퍼스널 트레이너입니다.\n"
    "입력으로 (1) 감지된 자세 오류와 심각도, (2) 측정 관측값·기준값, "
    "(3) 여러 관점에서 검색된 코칭 지식 문서가 주어집니다. "
    "이 참고 지식에만 근거해 사용자가 바로 따라 할 수 있는 코칭을 한국어 존댓말로 작성하세요.\n"
    "\n"
    "작성 규칙:\n"
    "- 근거: 참고 지식에 있는 내용만 사용하고, 없는 사실·수치·해부학 용어를 지어내지 마세요. "
    "지식이 부족하면 일반적이고 안전한 큐만 제시하세요.\n"
    "- 구조: ① 지금 무엇이 무너지고 있는지 한 문장으로 짚고 → ② 즉시 실행 가능한 교정 큐 "
    "1~2개를 구체적 신체 감각(예: '발뒤꿈치로 뒤쪽 벽을 민다')으로 제시하세요.\n"
    "- 심각도 반영: severity가 high면 더 단호하게(필요하면 자세를 풀고 다시 잡도록 안내), "
    "medium이면 또렷하게, low면 가볍게 다듬는 톤으로 조절하세요.\n"
    "- 수치를 그대로 나열하지 말고 '기준보다 골반이 처졌다'처럼 사용자가 이해할 표현으로 바꾸세요.\n"
    "- 여러 참고 문서가 서로 다른 관점(즉시 큐·원인·위험 등)을 담고 있으면 핵심만 골라 통합하세요.\n"
    "- 분량: 2~3문장. 부상 위험이 있을 때만 마지막에 '주의: ~' 한 줄을 덧붙이세요.\n"
    "- 마크다운 제목(##)이나 목록 기호 없이, 사람에게 말하듯 자연스러운 문장으로만 출력하세요."
)


@dataclass
class Coaching:
    error_code: str
    error_name: str
    severity: str
    comment: str
    retrieved_doc_ids: list[str] = field(default_factory=list)


def _format_context(docs: list[Document]) -> str:
    """검색된 문서를 번호·관점(variant)과 함께 블록으로 직렬화.

    v3 문서는 issue별로 즉시큐/원인/위험/심각도 등 관점이 나뉘어 있으므로,
    관점을 헤더에 노출해 LLM이 어떤 성격의 지식인지 알고 통합하도록 돕는다.
    """
    blocks = []
    for i, d in enumerate(docs, 1):
        m = d.metadata
        parts = [f"문서{i}", f"issue={m.get('issue_key')}"]
        if m.get("variant"):
            parts.append(f"관점={m.get('variant')}")
        if m.get("label"):
            parts.append(f"label={m.get('label')}")
        blocks.append(f"[{' | '.join(parts)}]\n{d.page_content}")
    return "\n\n".join(blocks)


def _build_prompt(eq: ErrorQuery, docs: list[Document]) -> str:
    observed = "\n".join(
        f"- {f}: 관측 {v}" + (f" (기준 {eq.threshold.get(f)})" if f in eq.threshold else "")
        for f, v in eq.observed.items()
    )
    return (
        f"## 감지된 오류\n{eq.error_name} ({eq.issue_key}), 심각도: {eq.severity}\n\n"
        f"## 관측값 (관측이 기준에서 벗어날수록 오류가 큼)\n{observed or '(제공된 수치 없음)'}\n\n"
        f"## 참고 코칭 지식 (아래 내용에만 근거하세요)\n{_format_context(docs)}\n\n"
        "위 오류에 대해, 시스템 규칙에 맞춰 사용자에게 전할 코칭 코멘트를 작성하세요."
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
