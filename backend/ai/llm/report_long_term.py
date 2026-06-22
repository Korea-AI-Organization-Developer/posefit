"""
리포트 "종합 평가" 전용 LangGraph.

사용자가 그동안 받은 자세 피드백(feedbacks.content) 기록 전체를 종합하여
장기적인 자세 경향·개선 방향을 평가한다. (langgraph_V1 의 long_term 경로를
리포트 화면에 맞춰 독립 모듈로 분리한 것 — chromadb 등 무거운 의존성 없음)

핵심 진입점: run_long_term_evaluation(feedback_texts, stats) -> dict | None
  - 동기 함수. FastAPI(async)에서는 asyncio.to_thread 로 호출한다.
  - GOOGLE_API_KEY / GEMINI_API_KEY 가 없으면 None 을 반환(→ 서비스가 규칙 기반으로 폴백).

반환 형식:
  {"summary": "...", "messages": [{"type": "positive|tip|warning", "text": "..."}]}
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, TypedDict

# langgraph/langchain 은 무겁고 선택적 의존성이므로 모듈 import 시점이 아니라
# 그래프를 실제로 쓸 때 lazy import 한다. (FastAPI 기동 속도·안정성 보호)

_VALID_TYPES = {"positive", "warning", "tip"}
_MAX_FEEDBACK_ITEMS = 60  # 프롬프트에 넣을 최근 피드백 최대 개수


class ReportEvalState(TypedDict, total=False):
    feedback_texts: List[str]
    stats: Dict[str, Any]
    api_key: str
    model: str
    llm_raw: str
    summary: str
    messages: List[Dict[str, str]]
    errors: List[str]


def _resolve_api_key(api_key: Optional[str]) -> Optional[str]:
    # 명시적으로 받은 키 우선, 없으면 환경변수(standalone 실행 대비).
    return api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def _get_llm(api_key: Optional[str], model: Optional[str]):
    """API 키가 있으면 Gemini LLM 을, 없으면 None 을 반환."""
    key = _resolve_api_key(api_key)
    if not key:
        return None

    from langchain_google_genai import ChatGoogleGenerativeAI

    model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    return ChatGoogleGenerativeAI(model=model_name, api_key=key, temperature=0.4)


def _build_prompt(feedback_texts: List[str], stats: Dict[str, Any]) -> str:
    sessions_count = stats.get("sessions_count")
    avg_score = stats.get("avg_score")
    best_exercise = stats.get("best_exercise")

    avg_text = f"{avg_score:.1f}점" if isinstance(avg_score, (int, float)) else "기록 없음"
    best_text = best_exercise or "기록 없음"

    numbered = "\n".join(
        f"{i + 1}. {text}"
        for i, text in enumerate(feedback_texts[:_MAX_FEEDBACK_ITEMS])
    )

    return (
        "당신은 운동 자세 코칭 전문 AI입니다.\n"
        "아래는 한 사용자가 그동안 운동하며 받은 자세 피드백 기록입니다.\n"
        "이 기록 전체를 종합하여, 사용자의 장기적인 자세 경향과 개선 방향을 평가하세요.\n\n"
        "=== 누적 통계 ===\n"
        f"총 운동 횟수: {sessions_count}회\n"
        f"평균 점수: {avg_text}\n"
        f"가장 잘하는 종목: {best_text}\n\n"
        "=== 피드백 기록 (최신순) ===\n"
        f"{numbered}\n\n"
        "=== 작성 규칙 ===\n"
        "- 반복적으로 나타나는 자세 문제를 찾아내세요.\n"
        "- 잘하고 있는 점(positive), 개선 팁(tip), 주의할 점(warning)을 균형 있게 제시하세요.\n"
        "- 각 메시지는 1~2문장의 친근한 한국어로 작성하세요.\n"
        "- 메시지는 3~5개로 작성하세요.\n"
        "- 기록에 없는 내용을 지어내지 마세요.\n\n"
        "반드시 아래 JSON 형식으로만 응답하세요:\n"
        '{"summary": "2~3문장 종합 평가", '
        '"messages": [{"type": "positive", "text": "..."}, {"type": "tip", "text": "..."}]}'
    )


def _evaluate_node(state: ReportEvalState) -> dict:
    feedback_texts = state.get("feedback_texts") or []
    stats = state.get("stats") or {}

    llm = _get_llm(state.get("api_key"), state.get("model"))
    if llm is None:
        return {"errors": ["LLM API 키가 설정되지 않았습니다."]}

    from langchain_core.messages import HumanMessage

    prompt = _build_prompt(feedback_texts, stats)
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
    except Exception as exc:  # noqa: BLE001 — 외부 호출 실패는 폴백으로 처리
        return {"errors": [f"LLM 호출 실패: {exc}"]}

    raw = response.content
    if isinstance(raw, list):
        raw = "\n".join(
            part["text"] for part in raw if isinstance(part, dict) and "text" in part
        )
    return {"llm_raw": str(raw)}


def _parse_node(state: ReportEvalState) -> dict:
    raw = state.get("llm_raw")
    if not raw:
        return {"messages": []}

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return {"messages": [], "errors": ["LLM 응답에서 JSON 을 찾지 못했습니다."]}

    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError as exc:
        return {"messages": [], "errors": [f"JSON 파싱 실패: {exc}"]}

    raw_messages = parsed.get("messages")
    messages: List[Dict[str, str]] = []
    if isinstance(raw_messages, list):
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            msg_type = str(item.get("type") or "").strip().lower()
            text = str(item.get("text") or "").strip()
            if msg_type not in _VALID_TYPES or not text:
                continue
            messages.append({"type": msg_type, "text": text})

    return {
        "summary": str(parsed.get("summary") or "").strip(),
        "messages": messages,
    }


_GRAPH = None


def _get_graph():
    """그래프를 1회만 컴파일해 캐싱한다."""
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH

    from langgraph.graph import StateGraph, START, END

    builder = StateGraph(ReportEvalState)
    builder.add_node("evaluate", _evaluate_node)
    builder.add_node("parse", _parse_node)
    builder.add_edge(START, "evaluate")
    builder.add_edge("evaluate", "parse")
    builder.add_edge("parse", END)

    _GRAPH = builder.compile()
    return _GRAPH


def run_long_term_evaluation(
    feedback_texts: List[str],
    stats: Dict[str, Any],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    LangGraph long-term 평가를 실행한다(동기).

    - API 키가 없거나 피드백이 없으면 None.
    - 그래프 실행/파싱 실패로 메시지가 비면 None → 서비스에서 규칙 기반으로 폴백.
    """
    if not feedback_texts:
        return None
    if not _resolve_api_key(api_key):
        return None

    graph = _get_graph()
    result = graph.invoke({
        "feedback_texts": feedback_texts,
        "stats": stats,
        "api_key": api_key or "",
        "model": model or "",
    })

    messages = result.get("messages") or []
    if not messages:
        return None

    return {"summary": result.get("summary", ""), "messages": messages}
