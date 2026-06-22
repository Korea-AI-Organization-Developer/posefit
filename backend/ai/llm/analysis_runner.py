"""
set 경로의 분석 단계만 실행해 analysis_result 를 산출한다.

전체 그래프(coaching_generator_node 의 chromadb RAG 포함) 대신
norm2feature → feature2seg → pose_decide_node 세 노드만 직접 호출하므로
chromadb 등 무거운 의존성 없이 구조화 자세분석 결과를 얻는다.

운동 세션 종료 시 호출 → 결과를 workout_analyses 에 저장한다.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

# 종목별 rule config 매핑. 현재 플랭크만 존재한다.
_RULE_CONFIG_BY_KEYWORD = {
    "plank": "config/plank_rule_config_mediapipe.json",
    "플랭크": "config/plank_rule_config_mediapipe.json",
}
_CONFIG_BASE = os.path.dirname(__file__)


def _resolve_rule_config(exercise_name: str | None) -> str | None:
    name = (exercise_name or "").lower()
    for keyword, rel in _RULE_CONFIG_BY_KEYWORD.items():
        if keyword in name:
            path = os.path.join(_CONFIG_BASE, rel)
            return path if os.path.exists(path) else None
    return None


def run_pose_analysis(
    normalized_pose: Dict[str, Any],
    exercise_name: str,
    camera_view: str = "측면",
) -> Optional[Dict[str, Any]]:
    """정규화 pose → analysis_result(dict). rule config 없으면 None.

    norm2feature/feature2seg/pose_decide_node 는 langgraph_V1 에 정의돼 있다.
    """
    rule_config_path = _resolve_rule_config(exercise_name)
    if rule_config_path is None:
        # 해당 종목 rule config 미존재(플랭크 외) → 분석 스킵
        return None

    from ai.llm.langgraph_V1 import norm2feature, feature2seg, pose_decide_node

    state: Dict[str, Any] = {
        "normalized_pose": normalized_pose,
        "exercise": exercise_name,
        "camera_view": camera_view,
        "rule_config_path": rule_config_path,
    }
    state.update(norm2feature(state))
    state.update(feature2seg(state))
    result = pose_decide_node(state)
    analysis = result.get("analysis_result")
    if not isinstance(analysis, dict):
        return None
    return _compact(analysis, exercise_name, camera_view)


def run_set_feedback(
    normalized_pose: Dict[str, Any],
    exercise_name: str,
    camera_view: str = "측면",
) -> str:
    """set 경로 전체 그래프 실행 → coaching 텍스트 반환.

    route_feedback 분기 조건:
    - today_set_results 없음 → "daily" 아님
    - historical_analysis_results / historical_feedback_texts 없음 → "long_term" 아님
    → 자동으로 "set" 경로로 분기됨
    """
    rule_config_path = _resolve_rule_config(exercise_name)
    if rule_config_path is None:
        return ""

    from ai.llm.langgraph_V1 import posefit_graph

    state: Dict[str, Any] = {
        "normalized_pose": normalized_pose,
        "exercise": exercise_name,
        "camera_view": camera_view,
        "rule_config_path": rule_config_path,
    }

    result = posefit_graph.invoke(state)
    feedback_text = result.get("final_feedback", {}).get("feedback_text", {})
    return feedback_text.get("coaching") or feedback_text.get("summary") or ""


def _compact(analysis: Dict[str, Any], exercise_name: str, camera_view: str) -> Dict[str, Any]:
    """장기 추세 평가에 필요한 핵심만 추려 저장(전체 result 는 수백 KB라 부적합)."""
    errors = [
        {
            "error_code": s.get("issue"),
            "error_name": s.get("description") or s.get("issue"),
            "severity": s.get("severity"),
            "occurrence_ratio": s.get("occurrence_ratio"),
        }
        for s in analysis.get("issue_summaries", [])
        if isinstance(s, dict)
    ]
    return {
        "exercise": exercise_name,
        "camera_view": camera_view,
        "overall_status": analysis.get("overall_status"),
        "segment_count": analysis.get("segment_count"),
        "errors": errors,
    }
