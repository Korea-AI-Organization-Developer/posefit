
import json
import operator
import os
import re
import subprocess
import sys
import time
from typing import TYPE_CHECKING, TypedDict, Annotated, List, Optional, Literal, Dict, Any

# langgraph 관련 라이브러리
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END

if TYPE_CHECKING:
    from langchain_google_genai import ChatGoogleGenerativeAI

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


def get_llm() -> "ChatGoogleGenerativeAI":
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY or GEMINI_API_KEY is required before calling an LLM node."
        )

    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=api_key)


class FeedbackState(TypedDict, total=False):
    # =========================================================
    # 0. Graph 시작 시 들어오는 공통 입력값
    # =========================================================
    user_id: str
    exercise: str              # 예: "플랭크"
    camera_view: str           # 예: "측면"
    date: str

    # =========================================================
    # 1. 현재 세트 입력값
    # - load_normalized_pose 노드 또는 graph 시작 입력에서 세팅
    # =========================================================
    video_id: str
    set_id: str
    set_number: int
    normalized_pose: Dict[str, Any]

    # =========================================================
    # 2. Feature Extractor 노드 output
    # 입력: normalized_pose
    # 출력: frame_features
    # 역할: 프레임별 각도/비율/신뢰도 계산
    # =========================================================
    frame_features: Optional[List[Dict[str, Any]]]

    # =========================================================
    # 3. Segment Aggregator 노드 output
    # 입력: frame_features
    # 출력: segment_features
    # 역할: 프레임별 feature를 window 단위로 요약
    # =========================================================
    segment_features: List[Dict[str, Any]]

    # =========================================================
    # 4. Rule Analyzer 노드 output
    # 입력: segment_features
    # 출력: analysis_result
    # 역할: 오류명, 오류 수준, 오류 부위, 발생 구간 판단
    # =========================================================
    analysis_result: Dict[str, Any]

    # =========================================================
    # 5. Coaching Generator 노드 output
    # 입력: analysis_result
    # 처리: RAG 검색 + LLM 코칭 생성
    # 출력: retrieved_docs, set_feedback
    # =========================================================
    retrieved_docs: List[Dict[str, Any]]
    set_feedback: Dict[str, Any]

    # =========================================================
    # 6. Daily Evaluator 노드 input/output
    # 입력: today_set_results, today_segment_features
    # 출력: daily_feedback
    # 역할: 오늘 수행한 전체 세트 평가
    # =========================================================
    today_set_results: List[Dict[str, Any]]
    today_feedbacks: List[Dict[str, Any]]
    feedbacks: List[Dict[str, Any]]
    today_segment_features: List[Dict[str, Any]]
    daily_feedback: Dict[str, Any]

    # =========================================================
    # 7. Long Term Evaluator 노드 input/output
    # 입력: historical_feedback_texts, historical_analysis_results
    # 출력: exercise_long_term_feedback
    # 역할: DB에 저장된 해당 운동 전체 기록 평가
    # =========================================================
    historical_feedback_texts: List[str]
    historical_analysis_results: Optional[List[Dict[str, Any]]]
    exercise_long_term_feedback: Dict[str, Any]

    # =========================================================
    # 8. Text Summarizer 노드 output
    # 입력: set_feedback, daily_feedback, exercise_long_term_feedback
    # 출력: feedback_text
    # 평가 노드 출력물 텍스트 정리
    # =========================================================
    feedback_text: Dict[str, str]

    # =========================================================
    # 9. Final Review / Feedback Refiner 노드 output
    # 입력: feedback_text
    # 출력: final_feedback
    # 역할: 최종 화면 출력용 피드백 구성
    # =========================================================
    final_feedback: Dict[str, Any]

    # =========================================================
    # 10. Error Handler
    # 각 노드에서 발생한 오류 메시지 누적
    # =========================================================
    errors: Annotated[List[str], operator.add]

# 분기노드
## 세트별 피드백, 운동 피드백, 종합 피드백 분기 노드
def branch_node(state: FeedbackState) -> dict:
    print("세트, 일일, 종합 입력값에 따라 분기하는 노드")
    return {}

# 분기 조건 함수
def route_feedback(state: FeedbackState) -> Literal["set", "daily", "long_term"]:
    if (
        state.get("today_set_results")
        or state.get("today_feedbacks")
        or state.get("feedbacks")
    ):
        return "daily"

    if state.get("historical_analysis_results"):
        return "long_term"

    return "set"


SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


def _enum_or_text(value: Any, default: str) -> str:
    if value is None:
        return default
    return str(getattr(value, "value", value)).strip() or default


def _normalize_severity(value: Any) -> str:
    severity = _enum_or_text(value, "info").lower()
    return severity if severity in SEVERITY_RANK else "info"


def _highest_severity(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "info"
    return max(
        (_normalize_severity(item.get("severity")) for item in items),
        key=lambda severity: SEVERITY_RANK[severity],
    )


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, dict):
        parts = [
            _clean_text(value.get(key))
            for key in ("summary", "main_issue", "coaching", "next_action", "content")
        ]
        return " ".join(part for part in parts if part)
    if isinstance(value, list):
        return " ".join(_clean_text(item) for item in value if _clean_text(item))
    return re.sub(r"\s+", " ", str(value)).strip()


def _first_text(mapping: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        text = _clean_text(mapping.get(key))
        if text:
            return text
    return ""


def _extract_feedback_text(mapping: Dict[str, Any]) -> str:
    text = _first_text(
        mapping,
        [
            "content",
            "comment",
            "message",
            "text",
            "feedback",
            "coaching",
            "summary",
        ],
    )
    if text:
        return text

    for nested_key in ("feedback_text", "final_feedback", "set_feedback", "daily_feedback"):
        nested = mapping.get(nested_key)
        if isinstance(nested, dict):
            text = _extract_feedback_text(nested)
            if text:
                return text
        else:
            text = _clean_text(nested)
            if text:
                return text

    return ""


def _iter_feedback_candidates(value: Any):
    if not value:
        return

    if isinstance(value, list):
        for item in value:
            yield from _iter_feedback_candidates(item)
        return

    if isinstance(value, dict):
        for nested_key in (
            "feedbacks",
            "today_feedbacks",
            "feedbackMessages",
            "feedback_messages",
            "messages",
            "comments",
        ):
            nested = value.get(nested_key)
            if isinstance(nested, list):
                for item in nested:
                    yield from _iter_feedback_candidates(item)

        yield value
        return

    yield value


def _normalize_feedback_item(raw: Any, position: int) -> Optional[Dict[str, Any]]:
    if isinstance(raw, dict):
        content = _extract_feedback_text(raw)
        if not content:
            return None

        generated_by = _enum_or_text(
            raw.get("generated_by") or raw.get("generatedBy") or raw.get("source"),
            "llm",
        ).lower()
        if generated_by not in {"rule", "llm"}:
            generated_by = "llm"

        return {
            "id": raw.get("id"),
            "session_id": raw.get("session_id") or raw.get("sessionId"),
            "set_id": raw.get("set_id") or raw.get("setId"),
            "set_number": raw.get("set_number") or raw.get("setNumber"),
            "severity": _normalize_severity(raw.get("severity")),
            "generated_by": generated_by,
            "content": content,
            "created_at": raw.get("created_at") or raw.get("createdAt"),
            "position": position,
        }

    content = _clean_text(raw)
    if not content:
        return None

    return {
        "id": None,
        "session_id": None,
        "set_id": None,
        "set_number": None,
        "severity": "info",
        "generated_by": "llm",
        "content": content,
        "created_at": None,
        "position": position,
    }


def _collect_today_feedbacks(state: FeedbackState) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen: set[tuple[Any, str]] = set()

    for state_key in ("today_feedbacks", "feedbacks", "today_set_results"):
        for position, raw in enumerate(_iter_feedback_candidates(state.get(state_key)), start=1):
            item = _normalize_feedback_item(raw, position)
            if not item:
                continue

            dedupe_key = (item.get("id"), item["content"])
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            items.append(item)

    return sorted(
        items,
        key=lambda item: (
            item.get("created_at") or "",
            item.get("id") if item.get("id") is not None else item["position"],
        ),
    )


def _take_texts(items: List[Dict[str, Any]], severities: set[str], limit: int) -> List[str]:
    texts: List[str] = []
    for item in items:
        if _normalize_severity(item.get("severity")) in severities:
            texts.append(item["content"])
        if len(texts) >= limit:
            break
    return texts


def _join_unique_texts(values: List[Any]) -> str:
    parts: List[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(text)
    return " ".join(parts)

# feature 추출 노드
## 영상으로부터 추출한 json파일을 초당 분리
### frame_features
def norm2feature(state: FeedbackState) -> dict:
    print("feature 추출 노드")
    return {"frame_features": []}

# Segment Aggregator 노드
## feature노드에서 추출된 feature를 단위로 묶음
### segment_features
def feature2seg(state: FeedbackState) -> dict:
    print("feature를 segment(window나 rap 단위로 묶는 노드)")
    return {"segment_features": []}

# 4. Rule Analyzer 노드 output
# 입력: segment_features
# 출력: analysis_result
# 역할: 오류명, 오류 수준, 오류 부위, 발생 구간 판단
def pose_decide_node(state:FeedbackState) -> dict:
    print("동작이 잘한 동작인지, 잘못한 동작인지, 어느 부분이 잘못된건지 판단하는 노드")
    return {
        "analysis_result": {
            "exercise": state.get("exercise"),
            "camera_view": state.get("camera_view"),
            "overall_status": "unknown",
            "errors": [],
            "strengths": [],
        }
    }


# =========================================================
# 5. Coaching Generator 노드 output
# 입력: analysis_result
# 처리: RAG 검색 + LLM 코칭 생성
# 출력: retrieved_docs, set_feedback
# =========================================================
def coaching_generator_node(state: FeedbackState) -> dict:
    # analysis_result = state["analysis_result"]

    # retrieved_docs = retrieve_coaching_docs(analysis_result)
    # set_feedback = generate_set_feedback(
    #     analysis_result=analysis_result,
    #     retrieved_docs=retrieved_docs,
    # )
    print("rag기반 답변 추출 노드")
    return {
        "retrieved_docs": [],
        "set_feedback": {
            "summary": "",
            "coaching": "",
            "source_error_codes": [],
        },
    }

# =========================================================
# 8. Text Summarizer 노드 output
# 입력: set_feedback
# 출력: feedback_text
# 평가 노드 출력물 텍스트 정리
# =========================================================
def set_text_summarize_node(state:FeedbackState) -> dict:
    print("평가 결과 text정리 노드")
    return {
        "feedback_text": {
            "summary": "",
            "main_issue": "",
            "coaching": "",
            "next_action": "",
        }
    }

# =========================================================
# 9. Final Review / Feedback Refiner 노드 output
# 입력: feedback_text
# 출력: final_feedback
# 역할: 최종 화면 출력용 피드백 구성
# =========================================================
def set_review_node(state:FeedbackState) -> dict:
    print("출력 텍스트 리뷰 노드")
    return {
        "final_feedback": {
            "type": "set",
            "feedback_text": state.get("feedback_text", {}),
        }
    }

# --------------------------------------------------------------------
# 일일 운동 평가 노드
# --------------------------------------------------------------------
# =========================================================
# 6. Daily Evaluator 노드 input/output
# 입력: today_set_results, today_segment_features
# 출력: daily_feedback
# 역할: 오늘 수행한 전체 세트 평가
# =========================================================
def daily_feedback_node(state: FeedbackState) -> dict:
    print("daily feedback node")
    feedbacks = _collect_today_feedbacks(state)
    feedback_count = len(feedbacks)
    warning_count = sum(
        1 for item in feedbacks if _normalize_severity(item.get("severity")) == "warning"
    )
    critical_count = sum(
        1 for item in feedbacks if _normalize_severity(item.get("severity")) == "critical"
    )
    info_count = sum(
        1 for item in feedbacks if _normalize_severity(item.get("severity")) == "info"
    )
    exercise = _clean_text(state.get("exercise")) or "오늘"

    issue_texts = _take_texts(feedbacks, {"warning", "critical"}, limit=3)
    positive_texts = _take_texts(feedbacks, {"info"}, limit=2)

    if feedback_count == 0:
        summary = "오늘 받은 피드백이 없습니다."
        next_action = "일일 요약을 받으려면 먼저 세트를 1개 이상 완료하세요."
    else:
        summary = f"오늘 {exercise} 운동의 피드백 {feedback_count}건을 종합했습니다."
        if critical_count or warning_count:
            next_action = "위에서 가장 중요한 교정 포인트부터 잡고 다음 세트를 시작하세요."
        else:
            next_action = "지금의 자세 패턴을 다음 세션에서도 그대로 유지하세요."

    return {
        "daily_feedback": {
            "summary": summary,
            "feedback_count": feedback_count,
            # 현재 일일 종합은 규칙 기반 집계다(LLM 미호출). LLM 코칭을 붙이면 "llm" 으로 바꾼다.
            "generated_by": "rule",
            "severity": _highest_severity(feedbacks),
            "severity_counts": {
                "info": info_count,
                "warning": warning_count,
                "critical": critical_count,
            },
            "repeated_errors": issue_texts,
            "strengths": positive_texts,
            "fatigue_trend": "",
            "next_action": next_action,
            "source_feedback_ids": [
                item["id"] for item in feedbacks if item.get("id") is not None
            ],
            "feedbacks": feedbacks,
        }
    }


def daily_text_summarize_node(state: FeedbackState) -> dict:
    print("daily text summarize node")
    daily_feedback = state.get("daily_feedback", {})
    feedbacks = daily_feedback.get("feedbacks", [])
    issue_texts = daily_feedback.get("repeated_errors", [])
    positive_texts = daily_feedback.get("strengths", [])

    summary = _clean_text(daily_feedback.get("summary"))
    main_issue = " ".join(issue_texts[:2])
    if not main_issue:
        main_issue = "오늘 피드백에서 큰 자세 문제는 발견되지 않았습니다."

    if positive_texts:
        coaching = positive_texts[0]
    elif issue_texts:
        coaching = "위 문제를 다음 세트의 우선 교정 포인트로 삼으세요."
    elif feedbacks:
        coaching = feedbacks[0]["content"]
    else:
        coaching = ""
    if not coaching:
        coaching = "아직 제공할 코칭 메시지가 없습니다."

    next_action = _clean_text(daily_feedback.get("next_action"))
    if not next_action:
        next_action = "다음 운동 전에 가장 최근 세트 피드백을 확인하세요."

    return {
        "feedback_text": {
            "summary": summary,
            "main_issue": main_issue,
            "coaching": coaching,
            "next_action": next_action,
        }
    }


def daily_review_node(state: FeedbackState) -> dict:
    print("daily review node")
    daily_feedback = state.get("daily_feedback", {})
    feedback_text = state.get("feedback_text", {})
    content = _join_unique_texts(
        [
            feedback_text.get("summary"),
            feedback_text.get("main_issue"),
            feedback_text.get("coaching"),
            feedback_text.get("next_action"),
        ]
    )
    severity = _normalize_severity(daily_feedback.get("severity"))
    # 생성 주체는 daily_feedback_node 가 정한 값을 따른다(현재 규칙 기반 → "rule").
    generated_by = _enum_or_text(daily_feedback.get("generated_by"), "rule").lower()
    if generated_by not in {"rule", "llm"}:
        generated_by = "rule"
    api_feedback = {
        "severity": severity,
        "generatedBy": generated_by,
        "content": content,
    }

    return {
        "final_feedback": {
            "type": "daily",
            "feedback_text": feedback_text,
            "feedback": api_feedback,
            "content": content,
            "severity": severity,
            "generated_by": generated_by,
            "generatedBy": generated_by,
            "source_feedback_ids": daily_feedback.get("source_feedback_ids", []),
            "feedback_count": daily_feedback.get("feedback_count", 0),
        }
    }


# --------------------------------------------------------------------
# 종합 운동 평가 노드
# --------------------------------------------------------------------
# =========================================================
# 7. Long Term Evaluator 노드 input/output
# 입력: historical_feedback_texts, historical_analysis_results
# 출력: exercise_long_term_feedback
# 역할: DB에 저장된 해당 운동 전체 기록 평가
# =========================================================
def long_term_feedback_node(state:FeedbackState) -> dict:
    print("종합운동 평가 노드")
    return {
        "exercise_long_term_feedback": {
            "summary": "",
            "improvement_trend": "",
            "long_term_issue": "",
        }
    }

def long_text_summarize_node(state:FeedbackState) -> dict:
    print("종합 평가 결과 text정리 노드")
    return {
        "feedback_text": {
            "summary": "",
            "main_issue": "",
            "coaching": "",
            "next_action": "",
        }
    }

def long_review_node(state:FeedbackState) -> dict:
    print("종합 평가 결과 출력 텍스트 리뷰 노드")
    return {
        "final_feedback": {
            "type": "long_term",
            "feedback_text": state.get("feedback_text", {}),
        }
    }

graph = StateGraph(FeedbackState)


graph.add_node("branch_node", branch_node)
graph.add_node("norm2feature", norm2feature)
graph.add_node("feature2seg", feature2seg)
graph.add_node("pose_decide_node", pose_decide_node)
graph.add_node("coaching_generator_node", coaching_generator_node)
graph.add_node("set_text_summarize_node", set_text_summarize_node)
graph.add_node("set_review_node", set_review_node)

# 일일 운동 평가
graph.add_node("daily_feedback_node", daily_feedback_node)
graph.add_node("daily_text_summarize_node", daily_text_summarize_node)
graph.add_node("daily_review_node", daily_review_node)

# 종합 운동 평가
graph.add_node("long_term_feedback_node", long_term_feedback_node)
graph.add_node("long_text_summarize_node", long_text_summarize_node)
graph.add_node("long_review_node", long_review_node)


graph.add_edge(START, "branch_node")

graph.add_conditional_edges(
    "branch_node",
    route_feedback,
    {
        "set": "norm2feature",
        "daily": "daily_feedback_node",
        "long_term": "long_term_feedback_node",
    },
)

graph.add_edge("norm2feature", "feature2seg")
graph.add_edge("feature2seg", "pose_decide_node")
graph.add_edge("pose_decide_node", "coaching_generator_node")
graph.add_edge("coaching_generator_node", "set_text_summarize_node")
graph.add_edge("set_text_summarize_node", "set_review_node")
graph.add_edge("set_review_node", END)

graph.add_edge("daily_feedback_node", "daily_text_summarize_node")
graph.add_edge("daily_text_summarize_node", "daily_review_node")
graph.add_edge("daily_review_node", END)

graph.add_edge("long_term_feedback_node", "long_text_summarize_node")
graph.add_edge("long_text_summarize_node", "long_review_node")
graph.add_edge("long_review_node", END)

posefit_graph = graph.compile()


# 그래프 구조 확인


def save_graph_image(path: str = "posefit_graph.png") -> None:
    from IPython.display import Image, display
    with open(path, "wb") as f:
        f.write(posefit_graph.get_graph().draw_mermaid_png())

if __name__ == "__main__":
    try:
        save_graph_image()
    except Exception as e:
        print(f"Failed to save graph image: {e}")
