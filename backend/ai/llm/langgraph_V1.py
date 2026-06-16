
import json
import operator
import os
import re
import subprocess
import sys
import time
from typing import TypedDict, Annotated, List, Optional, Literal, Dict, Any

# langgraph 관련 라이브러리
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


def get_llm() -> ChatGoogleGenerativeAI:
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
    if state.get("today_set_results"):
        return "daily"

    if state.get("historical_analysis_results"):
        return "long_term"

    return "set"

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
def daily_feedback_node(state:FeedbackState) -> dict:
    print("세트 종합 평가 노드")
    return {
        "daily_feedback": {
            "summary": "",
            "repeated_errors": [],
            "fatigue_trend": "",
        }
    }

def daily_text_summarize_node(state:FeedbackState) -> dict:
    print("세트 종합 평가 결과 text정리 노드")
    return {
        "feedback_text": {
            "summary": "",
            "main_issue": "",
            "coaching": "",
            "next_action": "",
        }
    }

def daily_review_node(state:FeedbackState) -> dict:
    print("세트 종합 평가 출력 텍스트 리뷰 노드")
    return {
        "final_feedback": {
            "type": "daily",
            "feedback_text": state.get("feedback_text", {}),
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
