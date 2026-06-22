
import json
import math
import operator
import os
import re
import subprocess
import sys
import time
from typing import TypedDict, Annotated, List, Optional, Literal, Dict, Any

import chromadb

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
    segment_unit: str
    window_seconds: float
    window_size_frames: int
    window_overlap_seconds: float
    window_overlap_frames: int
    rep_segments: List[Dict[str, Any]]

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
    # 리포트 종합 평가 입력 — 누적 통계 + LLM 키/모델(서비스가 주입)
    report_stats: Dict[str, Any]
    api_key: str
    model: str

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
    rule_config_path: str
    analysis_output_path: str

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

    # historical_analysis_results 또는 historical_feedback_texts 가 있으면 종합(long_term) 평가로 분기.
    # (리포트 화면은 누적 피드백 텍스트만으로 종합 평가를 요청한다)
    if state.get("historical_analysis_results") or state.get("historical_feedback_texts"):
        return "long_term"

    return "set"

# feature 추출 노드
## 영상으로부터 추출한 json파일을 초당 분리
### frame_features
# =========================================================
# Shared helpers for feature / segment / rule nodes
# - Used by: norm2feature, feature2seg, pose_decide_node
# =========================================================
def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _round(value: Optional[float], digits: int = 6) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


# =========================================================
# Node: norm2feature
# Input : normalized_pose
# Output: frame_features
#
# Helpers in this section are used to select visible joints and
# calculate per-frame pose geometry.
# =========================================================
def _point(keypoints: Dict[str, Any], name: str) -> Optional[Dict[str, float]]:
    keypoint = keypoints.get(name)
    if not isinstance(keypoint, dict):
        return None

    x = keypoint.get("x")
    y = keypoint.get("y")
    z = keypoint.get("z", 0.0)
    if not (_is_number(x) and _is_number(y) and _is_number(z)):
        return None

    return {"x": float(x), "y": float(y), "z": float(z)}


def _confidence(keypoints: Dict[str, Any], name: str) -> float:
    keypoint = keypoints.get(name)
    if not isinstance(keypoint, dict):
        return 0.0

    if keypoint.get("confidence_flag") == "excluded":
        return 0.0

    visibility = keypoint.get("visibility")
    presence = keypoint.get("presence")
    scores = [float(v) for v in (visibility, presence) if _is_number(v)]
    if not scores:
        return 1.0

    return max(0.0, min(scores))


def _choose_visible_side(keypoints: Dict[str, Any]) -> str:
    joints = ("shoulder", "elbow", "wrist", "hip", "knee", "ankle")
    side_scores = {}

    for side in ("left", "right"):
        scores = [_confidence(keypoints, f"{side}_{joint}") for joint in joints]
        side_scores[side] = sum(scores) / len(scores)

    return "left" if side_scores["left"] >= side_scores["right"] else "right"


def _distance(a: Dict[str, float], b: Dict[str, float]) -> float:
    return math.hypot(b["x"] - a["x"], b["y"] - a["y"])


def _angle(a: Dict[str, float], b: Dict[str, float], c: Dict[str, float]) -> Optional[float]:
    ba = (a["x"] - b["x"], a["y"] - b["y"])
    bc = (c["x"] - b["x"], c["y"] - b["y"])
    ba_len = math.hypot(*ba)
    bc_len = math.hypot(*bc)

    if ba_len == 0 or bc_len == 0:
        return None

    cosine = (ba[0] * bc[0] + ba[1] * bc[1]) / (ba_len * bc_len)
    cosine = max(-1.0, min(1.0, cosine))
    return math.degrees(math.acos(cosine))


def _line_angle(a: Dict[str, float], b: Dict[str, float]) -> Optional[float]:
    if a["x"] == b["x"] and a["y"] == b["y"]:
        return None
    return math.degrees(math.atan2(b["y"] - a["y"], b["x"] - a["x"])) % 360


def _angle_delta(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None:
        return None
    return (current - previous + 180) % 360 - 180


def _horizontal_tilt_angle(angle: Optional[float]) -> Optional[float]:
    if angle is None:
        return None
    return abs((float(angle) + 90) % 180 - 90)


def _line_deviation_ratio(
    point: Dict[str, float],
    line_start: Dict[str, float],
    line_end: Dict[str, float],
) -> Dict[str, Optional[float]]:
    line_length = _distance(line_start, line_end)
    if line_length == 0:
        return {
            "signed_ratio": None,
            "absolute_ratio": None,
        }

    dx = line_end["x"] - line_start["x"]
    dy = line_end["y"] - line_start["y"]
    cross = dx * (point["y"] - line_start["y"]) - dy * (point["x"] - line_start["x"])
    perpendicular_distance = abs(cross) / line_length

    if dx != 0:
        line_y = line_start["y"] + dy * ((point["x"] - line_start["x"]) / dx)
        sign = 1.0 if point["y"] >= line_y else -1.0
    else:
        sign = 1.0 if point["x"] >= line_start["x"] else -1.0

    ratio = perpendicular_distance / line_length
    return {
        "signed_ratio": sign * ratio,
        "absolute_ratio": ratio,
    }


def _load_normalized_pose(state: FeedbackState) -> Optional[Dict[str, Any]]:
    normalized_pose = state.get("normalized_pose")

    if isinstance(normalized_pose, dict):
        return normalized_pose

    if isinstance(normalized_pose, str):
        with open(normalized_pose, "r", encoding="utf-8") as f:
            return json.load(f)

    return None


# Node entrypoint: norm2feature
def norm2feature(state: FeedbackState) -> dict:
    print("feature 추출 노드")
    normalized_pose = _load_normalized_pose(state)
    if not normalized_pose:
        return {
            "frame_features": [],
            "errors": ["normalized_pose is missing or invalid."],
        }

    frames = normalized_pose.get("frames")
    if not isinstance(frames, list):
        return {
            "frame_features": [],
            "errors": ["normalized_pose.frames must be a list."],
        }

    fps = normalized_pose.get("fps")
    default_frame_ms = 1000.0 / float(fps) if _is_number(fps) and float(fps) > 0 else None

    frame_features: List[Dict[str, Any]] = []
    previous_valid: Optional[Dict[str, Any]] = None

    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue

        frame_id = frame.get("frame_id", index)
        timestamp_ms = frame.get("timestamp_ms")
        persons = frame.get("persons")

        base_feature: Dict[str, Any] = {
            "frame_id": frame_id,
            "timestamp_ms": timestamp_ms,
            "pose_detected": bool(frame.get("pose_detected")),
            "valid": False,
        }

        if not frame.get("pose_detected") or not isinstance(persons, list) or not persons:
            base_feature["invalid_reason"] = "pose_not_detected"
            frame_features.append(base_feature)
            continue

        person = persons[0]
        keypoints = person.get("keypoints") if isinstance(person, dict) else None
        if not isinstance(keypoints, dict):
            base_feature["invalid_reason"] = "keypoints_missing"
            frame_features.append(base_feature)
            continue

        side = _choose_visible_side(keypoints)
        joint_names = {
            "ear": f"{side}_ear",
            "shoulder": f"{side}_shoulder",
            "elbow": f"{side}_elbow",
            "wrist": f"{side}_wrist",
            "hip": f"{side}_hip",
            "knee": f"{side}_knee",
            "ankle": f"{side}_ankle",
        }

        points = {joint: _point(keypoints, name) for joint, name in joint_names.items()}
        if points["ear"] is None:
            points["ear"] = _point(keypoints, "nose")

        required = ("shoulder", "hip", "ankle")
        missing_required = [joint_names[joint] for joint in required if points[joint] is None]
        if missing_required:
            base_feature.update({
                "selected_side": side,
                "invalid_reason": "required_keypoints_missing",
                "missing_keypoints": missing_required,
            })
            frame_features.append(base_feature)
            continue

        shoulder = points["shoulder"]
        hip = points["hip"]
        ankle = points["ankle"]
        elbow = points["elbow"]
        wrist = points["wrist"]
        knee = points["knee"]
        ear = points["ear"]
        assert shoulder is not None and hip is not None and ankle is not None

        body_length = _distance(shoulder, ankle)
        body_line_angle = _line_angle(shoulder, ankle)
        hip_deviation = _line_deviation_ratio(hip, shoulder, ankle)
        head_deviation = _line_deviation_ratio(ear, shoulder, ankle) if ear else {
            "signed_ratio": None,
            "absolute_ratio": None,
        }
        shoulder_support_deviation = _line_deviation_ratio(shoulder, elbow, hip) if elbow else {
            "signed_ratio": None,
            "absolute_ratio": None,
        }
        lower_leg_angle = _line_angle(knee, ankle) if knee else None

        selected_keypoints = list(joint_names.values())
        confidence_scores = [_confidence(keypoints, name) for name in selected_keypoints]
        low_confidence_keypoints = [
            name
            for name in selected_keypoints
            if _confidence(keypoints, name) < 0.4
        ]

        feature: Dict[str, Any] = {
            "frame_id": frame_id,
            "timestamp_ms": timestamp_ms,
            "pose_detected": True,
            "valid": True,
            "selected_side": side,
            "feature_confidence": _round(sum(confidence_scores) / len(confidence_scores)),
            "low_confidence_keypoints": low_confidence_keypoints,
            "torso_line_angle": _round(body_line_angle),
            "body_line_angle": _round(body_line_angle),
            "body_line_tilt_angle": _round(_horizontal_tilt_angle(body_line_angle)),
            "shoulder_hip_ankle_angle": _round(_angle(shoulder, hip, ankle)),
            "hip_knee_ankle_angle": _round(_angle(hip, knee, ankle)) if knee else None,
            "shoulder_elbow_wrist_angle": _round(_angle(shoulder, elbow, wrist)) if elbow and wrist else None,
            "ear_shoulder_hip_angle": _round(_angle(ear, shoulder, hip)) if ear else None,
            "hip_sag_ratio": _round(hip_deviation["signed_ratio"]),
            "hip_line_deviation_ratio": _round(hip_deviation["absolute_ratio"]),
            "head_line_deviation_ratio": _round(head_deviation["signed_ratio"]),
            "head_drop_ratio": _round(
                max(0.0, float(head_deviation["signed_ratio"]))
                if _is_number(head_deviation["signed_ratio"])
                else None
            ),
            "head_rise_ratio": _round(
                max(0.0, -float(head_deviation["signed_ratio"]))
                if _is_number(head_deviation["signed_ratio"])
                else None
            ),
            "ankle_angle": _round(_horizontal_tilt_angle(lower_leg_angle)),
            "shoulder_support_deviation_ratio": _round(shoulder_support_deviation["signed_ratio"]),
            "shoulder_collapse_ratio": _round(
                -float(shoulder_support_deviation["signed_ratio"])
                if _is_number(shoulder_support_deviation["signed_ratio"])
                else None
            ),
            "body_length": _round(body_length),
            "torso_length": _round(_distance(shoulder, hip)),
            "leg_length": _round(_distance(hip, ankle)),
        }

        if previous_valid:
            previous_timestamp = previous_valid.get("timestamp_ms")
            if _is_number(timestamp_ms) and _is_number(previous_timestamp):
                elapsed_seconds = (float(timestamp_ms) - float(previous_timestamp)) / 1000.0
            elif default_frame_ms:
                elapsed_seconds = default_frame_ms / 1000.0
            else:
                elapsed_seconds = None

            previous_hip = previous_valid["_points"]["hip"]
            if elapsed_seconds and elapsed_seconds > 0:
                feature["hip_velocity"] = _round(_distance(hip, previous_hip) / elapsed_seconds)
            else:
                feature["hip_velocity"] = None

            feature["body_line_angle_delta"] = _round(_angle_delta(
                body_line_angle,
                previous_valid.get("body_line_angle"),
            ))
            feature["hip_sag_ratio_delta"] = _round(
                feature["hip_sag_ratio"] - previous_valid["hip_sag_ratio"]
                if feature["hip_sag_ratio"] is not None and previous_valid.get("hip_sag_ratio") is not None
                else None
            )
        else:
            feature["hip_velocity"] = None
            feature["body_line_angle_delta"] = None
            feature["hip_sag_ratio_delta"] = None

        previous_valid = {
            **feature,
            "_points": {
                "hip": hip,
            },
        }
        frame_features.append(feature)

    return {"frame_features": frame_features}


# =========================================================
# Node: feature2seg
# Input : frame_features
# Output: segment_features
#
# Helpers in this section split frames by time window, frame window,
# or rap/rep ranges, then summarize numeric features per segment.
# =========================================================
def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: List[float]) -> Optional[float]:
    if not values:
        return None

    mean_value = _mean(values)
    if mean_value is None:
        return None

    return math.sqrt(sum((value - mean_value) ** 2 for value in values) / len(values))


def _positive_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    return parsed if parsed > 0 else default


def _non_negative_float(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default

    return parsed if parsed >= 0 else default


def _estimate_fps(frame_features: List[Dict[str, Any]]) -> Optional[float]:
    timestamps = [
        float(feature["timestamp_ms"])
        for feature in frame_features
        if isinstance(feature, dict) and _is_number(feature.get("timestamp_ms"))
    ]
    if len(timestamps) < 2:
        return None

    deltas = [
        current - previous
        for previous, current in zip(timestamps, timestamps[1:])
        if current > previous
    ]
    if not deltas:
        return None

    average_delta_ms = sum(deltas) / len(deltas)
    return 1000.0 / average_delta_ms if average_delta_ms > 0 else None


def _segment_frames_by_count(
    frame_features: List[Dict[str, Any]],
    window_size: int,
    overlap: int,
) -> List[List[Dict[str, Any]]]:
    step = max(1, window_size - overlap)
    segments = []

    for start in range(0, len(frame_features), step):
        segment = frame_features[start:start + window_size]
        if segment:
            segments.append(segment)
        if start + window_size >= len(frame_features):
            break

    return segments


def _segment_frames_by_time(
    frame_features: List[Dict[str, Any]],
    window_seconds: float,
    overlap_seconds: float,
) -> List[List[Dict[str, Any]]]:
    timestamped = [
        feature
        for feature in frame_features
        if isinstance(feature, dict) and _is_number(feature.get("timestamp_ms"))
    ]
    if not timestamped:
        fps = _estimate_fps(frame_features)
        fallback_size = round(fps * window_seconds) if fps else 30
        fallback_overlap = round(fps * overlap_seconds) if fps else 0
        return _segment_frames_by_count(frame_features, max(1, fallback_size), max(0, fallback_overlap))

    window_ms = max(1.0, window_seconds * 1000.0)
    overlap_ms = min(max(0.0, overlap_seconds * 1000.0), window_ms - 1.0)
    step_ms = window_ms - overlap_ms
    min_timestamp = min(float(feature["timestamp_ms"]) for feature in timestamped)
    max_timestamp = max(float(feature["timestamp_ms"]) for feature in timestamped)

    segments = []
    start_timestamp = min_timestamp
    while start_timestamp <= max_timestamp:
        end_timestamp = start_timestamp + window_ms
        segment = [
            feature
            for feature in timestamped
            if start_timestamp <= float(feature["timestamp_ms"]) < end_timestamp
        ]
        if segment:
            segments.append(segment)
        start_timestamp += step_ms

    return segments


def _segment_frames_by_rep(
    frame_features: List[Dict[str, Any]],
    rep_segments: List[Dict[str, Any]],
) -> List[List[Dict[str, Any]]]:
    segments = []

    for rep in rep_segments:
        if not isinstance(rep, dict):
            continue

        start_frame = rep.get("start_frame_id", rep.get("start_frame"))
        end_frame = rep.get("end_frame_id", rep.get("end_frame"))
        start_timestamp = rep.get("start_timestamp_ms")
        end_timestamp = rep.get("end_timestamp_ms")

        if _is_number(start_frame) and _is_number(end_frame):
            segment = [
                feature
                for feature in frame_features
                if _is_number(feature.get("frame_id"))
                and float(start_frame) <= float(feature["frame_id"]) <= float(end_frame)
            ]
        elif _is_number(start_timestamp) and _is_number(end_timestamp):
            segment = [
                feature
                for feature in frame_features
                if _is_number(feature.get("timestamp_ms"))
                and float(start_timestamp) <= float(feature["timestamp_ms"]) <= float(end_timestamp)
            ]
        else:
            segment = []

        if segment:
            segments.append(segment)

    return segments


def _summarize_segment(
    segment_frames: List[Dict[str, Any]],
    segment_id: int,
    segment_type: str,
) -> Dict[str, Any]:
    valid_frames = [feature for feature in segment_frames if feature.get("valid")]
    first_frame = segment_frames[0]
    last_frame = segment_frames[-1]
    summary: Dict[str, Any] = {
        "segment_id": segment_id,
        "window_id": segment_id,
        "segment_type": segment_type,
        "start_frame_id": first_frame.get("frame_id"),
        "end_frame_id": last_frame.get("frame_id"),
        "start_timestamp_ms": first_frame.get("timestamp_ms"),
        "end_timestamp_ms": last_frame.get("timestamp_ms"),
        "frame_count": len(segment_frames),
        "valid_frame_count": len(valid_frames),
        "invalid_frame_count": len(segment_frames) - len(valid_frames),
        "valid_ratio": _round(len(valid_frames) / len(segment_frames)),
    }

    side_counts: Dict[str, int] = {}
    low_confidence_counts: Dict[str, int] = {}

    for feature in valid_frames:
        side = feature.get("selected_side")
        if isinstance(side, str):
            side_counts[side] = side_counts.get(side, 0) + 1

        for keypoint in feature.get("low_confidence_keypoints", []):
            if isinstance(keypoint, str):
                low_confidence_counts[keypoint] = low_confidence_counts.get(keypoint, 0) + 1

    summary["selected_side_counts"] = side_counts
    summary["low_confidence_keypoint_counts"] = low_confidence_counts

    excluded_keys = {"frame_id", "timestamp_ms"}
    numeric_keys = sorted({
        key
        for feature in valid_frames
        for key, value in feature.items()
        if key not in excluded_keys and _is_number(value)
    })

    for key in numeric_keys:
        values = [
            float(feature[key])
            for feature in valid_frames
            if _is_number(feature.get(key))
        ]
        if not values:
            continue

        summary[f"{key}_mean"] = _round(_mean(values))
        summary[f"{key}_min"] = _round(min(values))
        summary[f"{key}_max"] = _round(max(values))
        summary[f"{key}_std"] = _round(_std(values))

    return summary

# Segment Aggregator 노드
## feature노드에서 추출된 feature를 단위로 묶음
### segment_features
def _default_segment_unit_for_exercise(exercise: Any) -> str:
    exercise_name = str(exercise or "").strip().lower()
    if "plank" in exercise_name or "플랭크" in exercise_name:
        return "window"
    return "rap"


def _normalize_segment_unit(segment_unit: Any) -> str:
    normalized = str(segment_unit or "").strip().lower()

    if normalized in {"window", "second", "seconds", "sec", "time"}:
        return "window"
    if normalized in {"frame", "frames"}:
        return "frame"
    if normalized in {"rap", "rep", "reps"}:
        return "rap"

    return normalized


# Node entrypoint: feature2seg
def feature2seg(state: FeedbackState) -> dict:
    print("feature를 segment(window나 rap 단위로 묶는 노드)")
    frame_features = state.get("frame_features")
    if not isinstance(frame_features, list):
        return {
            "segment_features": [],
            "errors": ["frame_features must be a list."],
        }

    if not frame_features:
        return {"segment_features": []}

    default_segment_unit = _default_segment_unit_for_exercise(state.get("exercise"))
    requested_segment_unit = state.get("segment_unit")
    segment_unit = _normalize_segment_unit(requested_segment_unit or default_segment_unit)

    errors: List[str] = []
    if segment_unit == "frame":
        fps = _estimate_fps(frame_features)
        default_window = round(fps) if fps else 30
        window_size = _positive_int(state.get("window_size_frames"), default_window)
        overlap = min(_positive_int(state.get("window_overlap_frames"), 0), window_size - 1)
        raw_segments = _segment_frames_by_count(frame_features, window_size, overlap)
        segment_type = "frame_window"
    elif segment_unit == "rap":
        rep_segments = state.get("rep_segments", [])
        if not isinstance(rep_segments, list) or not rep_segments:
            return {
                "segment_unit": segment_unit,
                "segment_features": [],
                "errors": ["rep_segments is required when segment_unit='rap'."],
            }
        raw_segments = _segment_frames_by_rep(frame_features, rep_segments)
        segment_type = "rap"
    else:
        if segment_unit != "window":
            errors.append(f"Unknown segment_unit '{segment_unit}', using 'window'.")
        segment_unit = "window"
        window_seconds = _non_negative_float(state.get("window_seconds"), 1.0)
        if window_seconds == 0:
            window_seconds = 1.0
        overlap_seconds = _non_negative_float(state.get("window_overlap_seconds"), 0.0)
        raw_segments = _segment_frames_by_time(frame_features, window_seconds, overlap_seconds)
        segment_type = "time_window"

    segment_features = [
        _summarize_segment(segment, index, segment_type)
        for index, segment in enumerate(raw_segments)
        if segment
    ]

    result = {
        "segment_unit": segment_unit,
        "segment_features": segment_features,
    }
    if errors:
        result["errors"] = errors
    return result

# 4. Rule Analyzer 노드 output
# 입력: segment_features
# 출력: analysis_result
# 역할: 오류명, 오류 수준, 오류 부위, 발생 구간 판단
# =========================================================
# Node: pose_decide_node
# Input : segment_features
# Output: analysis_result
#
# Helpers in this section load the rule config, map config feature
# names to segment feature keys, evaluate conditions, and summarize
# triggered posture issues.
# =========================================================
DEFAULT_RULE_CONFIG_PATH = os.path.join("config", "plank_rule_config_mediapipe.json")


def _exercise_rule_key(exercise: Any) -> str:
    exercise_name = str(exercise or "").strip().lower()
    if "plank" in exercise_name or "플랭크" in exercise_name:
        return "plank"
    return exercise_name


def _camera_view_rule_key(camera_view: Any) -> str:
    view = str(camera_view or "").strip().lower()
    if not view:
        return "side"
    if "side" in view or "측" in view or "옆" in view:
        return "side"
    if "front" in view or "정면" in view:
        return "front"
    return view


def _load_rule_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _finalize_pose_decision(
    analysis_result: Dict[str, Any],
    output_path: Optional[str],
) -> Dict[str, Any]:
    if output_path:
        analysis_result["analysis_output_path"] = output_path
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({"analysis_result": analysis_result}, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            technical_errors = analysis_result.setdefault("technical_errors", [])
            if isinstance(technical_errors, list):
                technical_errors.append(f"Failed to save analysis output: {exc}")

    return {"analysis_result": analysis_result}


def _compare_rule_value(value: float, operator_name: str, threshold: float) -> bool:
    if operator_name == "<":
        return value < threshold
    if operator_name == "<=":
        return value <= threshold
    if operator_name == ">":
        return value > threshold
    if operator_name == ">=":
        return value >= threshold
    if operator_name == "==":
        return value == threshold
    if operator_name == "!=":
        return value != threshold
    raise ValueError(f"Unsupported operator: {operator_name}")


def _operator_suffix_order(operator_name: str) -> List[str]:
    if operator_name in {">", ">="}:
        return ["_max", "_mean", ""]
    if operator_name in {"<", "<="}:
        return ["_min", "_mean", ""]
    return ["_mean", "", "_max", "_min"]


def _segment_direct_value(
    segment: Dict[str, Any],
    feature: str,
    operator_name: str,
) -> Optional[Dict[str, Any]]:
    for suffix in _operator_suffix_order(operator_name):
        key = f"{feature}{suffix}" if suffix else feature
        value = segment.get(key)
        if _is_number(value):
            return {
                "value": float(value),
                "source_key": key,
            }
    return None


def _segment_range_value(segment: Dict[str, Any], base_feature: str) -> Optional[Dict[str, Any]]:
    min_key = f"{base_feature}_min"
    max_key = f"{base_feature}_max"
    min_value = segment.get(min_key)
    max_value = segment.get(max_key)
    if not (_is_number(min_value) and _is_number(max_value)):
        return None

    return {
        "value": float(max_value) - float(min_value),
        "source_key": f"{max_key}-{min_key}",
    }


def _segment_signed_ratio_value(
    segment: Dict[str, Any],
    feature: str,
    operator_name: str,
) -> Optional[Dict[str, Any]]:
    mean_value = segment.get("hip_sag_ratio_mean")
    min_value = segment.get("hip_sag_ratio_min")
    max_value = segment.get("hip_sag_ratio_max")

    if feature == "hip_drop_ratio":
        if _is_number(mean_value):
            return {
                "value": max(0.0, float(mean_value)),
                "source_key": "derived:hip_sag_ratio_mean",
            }
        if operator_name in {">", ">="} and _is_number(max_value):
            return {
                "value": max(0.0, float(max_value)),
                "source_key": "derived:hip_sag_ratio_max",
            }

    if feature == "hip_pike_ratio":
        if _is_number(mean_value):
            return {
                "value": max(0.0, -float(mean_value)),
                "source_key": "derived:-hip_sag_ratio_mean",
            }
        if operator_name in {">", ">="} and _is_number(min_value):
            return {
                "value": max(0.0, -float(min_value)),
                "source_key": "derived:-hip_sag_ratio_min",
            }

    return None


def _resolve_rule_feature_value(
    segment: Dict[str, Any],
    feature: str,
    operator_name: str,
) -> Optional[Dict[str, Any]]:
    if feature == "body_line_angle":
        return _segment_direct_value(segment, "shoulder_hip_ankle_angle", operator_name)

    if feature == "body_line_angle_std":
        value = segment.get("shoulder_hip_ankle_angle_std")
        if _is_number(value):
            return {
                "value": float(value),
                "source_key": "shoulder_hip_ankle_angle_std",
            }

    if feature == "body_line_angle_range":
        return _segment_range_value(segment, "shoulder_hip_ankle_angle")

    if feature in {"hip_drop_ratio", "hip_pike_ratio"}:
        return _segment_signed_ratio_value(segment, feature, operator_name)

    if feature == "torso_horizontal_angle":
        return _segment_direct_value(segment, "body_line_tilt_angle", operator_name)

    if feature == "elbow_angle":
        return _segment_direct_value(segment, "shoulder_elbow_wrist_angle", operator_name)

    return _segment_direct_value(segment, feature, operator_name)


def _evaluate_rule_condition(
    segment: Dict[str, Any],
    condition: Dict[str, Any],
) -> Dict[str, Any]:
    feature = str(condition.get("feature", ""))
    operator_name = str(condition.get("operator", ""))
    threshold = condition.get("threshold")

    result: Dict[str, Any] = {
        "feature": feature,
        "operator": operator_name,
        "threshold": threshold,
        "matched": False,
    }

    if not feature or not operator_name or not _is_number(threshold):
        result["missing_reason"] = "invalid_condition"
        return result

    resolved = _resolve_rule_feature_value(segment, feature, operator_name)
    if not resolved:
        result["missing_reason"] = "feature_missing"
        return result

    value = float(resolved["value"])
    result.update({
        "value": _round(value),
        "source_key": resolved["source_key"],
        "matched": _compare_rule_value(value, operator_name, float(threshold)),
    })
    return result


def _rule_severity(triggered_count: int, segment_count: int) -> str:
    if segment_count <= 0:
        return "unknown"

    ratio = triggered_count / segment_count
    if ratio >= 0.5:
        return "high"
    if ratio >= 0.2:
        return "medium"
    return "low"


def _time_range_from_segment(segment: Dict[str, Any]) -> Dict[str, Optional[float]]:
    start_ms = segment.get("start_timestamp_ms")
    end_ms = segment.get("end_timestamp_ms")
    return {
        "start_sec": _round(float(start_ms) / 1000.0, 3) if _is_number(start_ms) else None,
        "end_sec": _round(float(end_ms) / 1000.0, 3) if _is_number(end_ms) else None,
    }


def _condition_values(
    condition_results: List[Dict[str, Any]],
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, str]]:
    observed_values: Dict[str, Any] = {}
    threshold_values: Dict[str, Any] = {}
    threshold_operators: Dict[str, str] = {}

    for condition in condition_results:
        feature = condition.get("feature")
        if not isinstance(feature, str) or not feature:
            continue

        value = condition.get("value")
        threshold = condition.get("threshold")
        operator_name = condition.get("operator")

        if _is_number(value):
            observed_values[feature] = _round(float(value))
        if _is_number(threshold):
            threshold_values[feature] = _round(float(threshold))
        if isinstance(operator_name, str) and operator_name:
            threshold_operators[feature] = operator_name

    return observed_values, threshold_values, threshold_operators


def _window_error_from_trigger(
    issue: Dict[str, Any],
    triggered: Dict[str, Any],
    severity: str,
) -> Dict[str, Any]:
    condition_results = [
        condition
        for condition in triggered.get("conditions", [])
        if isinstance(condition, dict)
    ]
    matched_condition_results = [
        condition
        for condition in condition_results
        if condition.get("matched")
    ]
    observed_values, threshold_values, threshold_operators = _condition_values(
        matched_condition_results or condition_results
    )

    error_code = issue.get("issue")
    error_name = issue.get("description") or error_code

    return {
        "error_code": error_code,
        "issue": error_code,
        "error_name": error_name,
        "description": error_name,
        "phase": issue.get("phase"),
        "window_id": triggered.get("window_id"),
        "segment_id": triggered.get("segment_id"),
        "severity": severity,
        "observed_values": observed_values,
        "threshold_values": threshold_values,
        "threshold_operators": threshold_operators,
        "time_range": _time_range_from_segment(triggered),
        "start_frame_id": triggered.get("start_frame_id"),
        "end_frame_id": triggered.get("end_frame_id"),
        "matched_conditions": matched_condition_results,
    }


def _window_lookup_key(window_id: Any) -> str:
    return str(window_id)


def _segment_window_id(segment: Dict[str, Any], fallback_index: int) -> Any:
    if segment.get("window_id") is not None:
        return segment.get("window_id")
    if segment.get("segment_id") is not None:
        return segment.get("segment_id")
    return fallback_index


def _build_window_results(
    segment_features: List[Dict[str, Any]],
    window_errors_by_id: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    window_results: List[Dict[str, Any]] = []

    for index, segment in enumerate(segment_features):
        if not isinstance(segment, dict):
            continue

        window_id = _segment_window_id(segment, index)
        errors = window_errors_by_id.get(_window_lookup_key(window_id), [])
        window_results.append({
            "window_id": window_id,
            "segment_id": segment.get("segment_id"),
            "status": "needs_correction" if errors else "correct",
            "time_range": _time_range_from_segment(segment),
            "start_frame_id": segment.get("start_frame_id"),
            "end_frame_id": segment.get("end_frame_id"),
            "valid_ratio": segment.get("valid_ratio"),
            "errors": errors,
        })

    return window_results


def _build_strengths(
    window_results: List[Dict[str, Any]],
    passed_rules: List[str],
) -> List[Dict[str, Any]]:
    strengths: List[Dict[str, Any]] = []
    correct_windows = [
        window
        for window in window_results
        if window.get("status") == "correct"
    ]

    if correct_windows:
        strengths.append({
            "name": "correct_windows",
            "description": "자세 오류가 감지되지 않은 구간입니다.",
            "window_ids": [window.get("window_id") for window in correct_windows],
            "time_ranges": [window.get("time_range") for window in correct_windows],
        })

    if passed_rules:
        strengths.append({
            "name": "configured_rules_passed",
            "passed_rules": passed_rules,
        })

    return strengths


def _summarize_triggered_issue(
    issue: Dict[str, Any],
    triggered_segments: List[Dict[str, Any]],
    segment_count: int,
) -> Dict[str, Any]:
    observed_values: Dict[str, Dict[str, Optional[float]]] = {}
    threshold_values: Dict[str, Any] = {}

    for triggered in triggered_segments:
        for condition in triggered.get("conditions", []):
            feature = condition.get("feature")
            value = condition.get("value")
            if not isinstance(feature, str) or not _is_number(value):
                continue

            values = observed_values.setdefault(feature, {
                "min": None,
                "max": None,
                "mean": None,
                "count": 0,
                "_sum": 0.0,
            })
            numeric_value = float(value)
            values["min"] = numeric_value if values["min"] is None else min(values["min"], numeric_value)
            values["max"] = numeric_value if values["max"] is None else max(values["max"], numeric_value)
            values["_sum"] = float(values["_sum"]) + numeric_value
            values["count"] = int(values["count"]) + 1
            threshold_values[feature] = {
                "operator": condition.get("operator"),
                "threshold": condition.get("threshold"),
            }

    for feature_values in observed_values.values():
        count = int(feature_values["count"])
        feature_values["mean"] = _round(float(feature_values["_sum"]) / count) if count else None
        feature_values["min"] = _round(feature_values["min"])
        feature_values["max"] = _round(feature_values["max"])
        del feature_values["_sum"]

    return {
        "issue": issue.get("issue"),
        "description": issue.get("description"),
        "phase": issue.get("phase"),
        "severity": _rule_severity(len(triggered_segments), segment_count),
        "condition_logic": issue.get("condition_logic", "AND"),
        "occurrence_count": len(triggered_segments),
        "occurrence_ratio": _round(len(triggered_segments) / segment_count) if segment_count else None,
        "segment_ids": [segment.get("segment_id") for segment in triggered_segments],
        "observed_values": observed_values,
        "threshold_values": threshold_values,
        "triggered_segments": triggered_segments,
    }


# Node entrypoint: pose_decide_node
def pose_decide_node(state:FeedbackState) -> dict:
    print("동작이 잘한 동작인지, 잘못한 동작인지, 어느 부분이 잘못된건지 판단하는 노드")
    exercise = state.get("exercise")
    camera_view = state.get("camera_view")
    segment_features = state.get("segment_features")
    rule_config_path = str(state.get("rule_config_path") or DEFAULT_RULE_CONFIG_PATH)
    analysis_output_path = state.get("analysis_output_path")
    if analysis_output_path is not None:
        analysis_output_path = str(analysis_output_path)

    analysis_result: Dict[str, Any] = {
        "exercise": exercise,
        "camera_view": camera_view,
        "rule_config_path": rule_config_path,
        "overall_status": "unknown",
        "errors": [],
        "strengths": [],
        "skipped_rules": [],
        "missing_features": [],
    }

    if not isinstance(segment_features, list):
        analysis_result["technical_errors"] = ["segment_features must be a list."]
        return _finalize_pose_decision(analysis_result, analysis_output_path)

    if not segment_features:
        analysis_result["technical_errors"] = ["segment_features is empty."]
        return _finalize_pose_decision(analysis_result, analysis_output_path)

    try:
        rule_config = _load_rule_config(rule_config_path)
    except Exception as exc:
        analysis_result["technical_errors"] = [f"Failed to load rule config: {exc}"]
        return _finalize_pose_decision(analysis_result, analysis_output_path)

    exercise_key = _exercise_rule_key(exercise)
    view_key = _camera_view_rule_key(camera_view)
    exercise_rules = rule_config.get(exercise_key)
    view_rules = exercise_rules.get(view_key) if isinstance(exercise_rules, dict) else None
    issues = view_rules.get("issues") if isinstance(view_rules, dict) else None

    if not isinstance(issues, list):
        analysis_result["technical_errors"] = [
            f"No rules found for exercise='{exercise_key}', camera_view='{view_key}'."
        ]
        return _finalize_pose_decision(analysis_result, analysis_output_path)

    missing_features: Dict[str, int] = {}
    skipped_rules: List[Dict[str, Any]] = []
    issue_summaries: List[Dict[str, Any]] = []
    window_errors_by_id: Dict[str, List[Dict[str, Any]]] = {}
    passed_rules: List[str] = []

    for issue in issues:
        if not isinstance(issue, dict):
            continue

        condition_logic = str(issue.get("condition_logic", "AND")).upper()
        conditions = issue.get("conditions", [])
        min_confidence = issue.get("min_confidence", 0.0)
        triggered_segments = []
        skipped_low_confidence = []

        if not isinstance(conditions, list) or not conditions:
            skipped_rules.append({
                "issue": issue.get("issue"),
                "reason": "conditions_missing",
            })
            continue

        for segment in segment_features:
            if not isinstance(segment, dict):
                continue

            confidence = segment.get("feature_confidence_mean", 1.0)
            if _is_number(min_confidence) and _is_number(confidence) and float(confidence) < float(min_confidence):
                skipped_low_confidence.append(segment.get("segment_id"))
                continue

            condition_results = [
                _evaluate_rule_condition(segment, condition)
                for condition in conditions
                if isinstance(condition, dict)
            ]
            for condition_result in condition_results:
                if condition_result.get("missing_reason") == "feature_missing":
                    feature = str(condition_result.get("feature"))
                    missing_features[feature] = missing_features.get(feature, 0) + 1

            matches = [bool(result.get("matched")) for result in condition_results]
            if condition_logic == "OR":
                is_triggered = any(matches)
            else:
                is_triggered = bool(matches) and all(matches)

            if is_triggered:
                triggered_segments.append({
                    "segment_id": segment.get("segment_id"),
                    "window_id": segment.get("window_id"),
                    "start_frame_id": segment.get("start_frame_id"),
                    "end_frame_id": segment.get("end_frame_id"),
                    "start_timestamp_ms": segment.get("start_timestamp_ms"),
                    "end_timestamp_ms": segment.get("end_timestamp_ms"),
                    "conditions": condition_results,
                })

        if skipped_low_confidence:
            skipped_rules.append({
                "issue": issue.get("issue"),
                "reason": "low_confidence",
                "segment_ids": skipped_low_confidence,
            })

        if triggered_segments:
            issue_summary = _summarize_triggered_issue(
                issue,
                triggered_segments,
                len(segment_features),
            )
            issue_summaries.append(issue_summary)

            for triggered in triggered_segments:
                window_error = _window_error_from_trigger(
                    issue=issue,
                    triggered=triggered,
                    severity=str(issue_summary.get("severity") or "unknown"),
                )
                window_key = _window_lookup_key(window_error.get("window_id"))
                window_errors_by_id.setdefault(window_key, []).append(window_error)
        else:
            issue_name = issue.get("issue")
            if isinstance(issue_name, str):
                passed_rules.append(issue_name)

    window_results = _build_window_results(segment_features, window_errors_by_id)
    window_errors = [
        error
        for window in window_results
        for error in window.get("errors", [])
        if isinstance(error, dict)
    ]
    window_errors.sort(key=lambda error: (
        (error.get("time_range") or {}).get("start_sec")
        if _is_number((error.get("time_range") or {}).get("start_sec"))
        else float("inf"),
        str(error.get("error_code") or ""),
    ))

    analysis_result.update({
        "exercise_rule_key": exercise_key,
        "camera_view_rule_key": view_key,
        "rule_count": len(issues),
        "segment_count": len(segment_features),
        "overall_status": "needs_correction" if window_errors else "correct",
        "errors": window_errors,
        "issue_summaries": issue_summaries,
        "window_results": window_results,
        "strengths": _build_strengths(window_results, passed_rules),
        "skipped_rules": skipped_rules,
        "missing_features": [
            {
                "feature": feature,
                "count": count,
            }
            for feature, count in sorted(missing_features.items())
        ],
    })

    return _finalize_pose_decision(analysis_result, analysis_output_path)


# =========================================================
# 5. Coaching Generator 노드 output
# 입력: analysis_result
# 처리: RAG 검색 + LLM 코칭 생성
# 출력: retrieved_docs, set_feedback
# =========================================================

CHROMA_PATH = ".chroma"
CHROMA_COLLECTION = "posefit_coaching"

# variant 우선순위 — 가장 코칭에 직접 쓸 수 있는 섹션
_CORE_VARIANTS = {"01_core_alignment", "02_immediate_cues"}
_SEVERITY_VARIANT = {
    "low": "09_severity_low",
    "medium": "10_severity_medium",
    "high": "11_severity_high",
}


def _view_to_kr(camera_view: str) -> str:
    v = str(camera_view or "").strip().lower()
    if "side" in v or "측" in v or "옆" in v:
        return "측면"
    if "front" in v or "정면" in v:
        return "정면"
    return ""


def _retrieve_coaching_docs(
    errors: List[Dict[str, Any]],
    camera_view: str,
) -> List[Dict[str, Any]]:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(CHROMA_COLLECTION)

    view_kr = _view_to_kr(camera_view)
    retrieved: List[Dict[str, Any]] = []
    seen_requests: set[tuple[str, str]] = set()

    for error in errors:
        error_code = str(error.get("error_code") or error.get("issue") or "").strip()
        severity = str(error.get("severity") or "medium")
        if not error_code:
            continue

        request_key = (error_code, severity)
        if request_key in seen_requests:
            continue
        seen_requests.add(request_key)

        preferred = _CORE_VARIANTS | {_SEVERITY_VARIANT.get(severity, "10_severity_medium")}

        where_filter: Dict[str, Any]
        if view_kr:
            where_filter = {
                "$and": [
                    {"issue_key": {"$eq": error_code}},
                    {"view": {"$eq": view_kr}},
                ]
            }
        else:
            where_filter = {"issue_key": {"$eq": error_code}}

        results = collection.get(
            where=where_filter,
            include=["documents", "metadatas"],
        )

        primary_doc: Optional[Dict[str, Any]] = None
        variant_docs: List[Dict[str, Any]] = []

        for doc, meta in zip(results["documents"], results["metadatas"]):
            variant = meta.get("variant") or ""
            chunk = meta.get("chunk")
            entry = {
                "error_code": error_code,
                "severity": severity,
                "document": doc,
                "metadata": meta,
            }
            if not variant and chunk == 0:
                primary_doc = entry
            elif variant in preferred:
                variant_docs.append(entry)

        # variant 문서 우선, 없으면 chunk 0 으로 fallback
        selected = variant_docs if variant_docs else ([primary_doc] if primary_doc else [])
        retrieved.extend(selected)

    return retrieved


def _error_code(error: Dict[str, Any]) -> str:
    return str(error.get("error_code") or error.get("issue") or "").strip()


def _error_name(error: Dict[str, Any]) -> str:
    return str(error.get("error_name") or error.get("description") or _error_code(error)).strip()


def _format_seconds(value: Any) -> str:
    if not _is_number(value):
        return "알 수 없는 시점"
    seconds = round(float(value), 1)
    if seconds.is_integer():
        return str(int(seconds))
    return str(seconds)


def _format_time_range(time_range: Dict[str, Any]) -> str:
    start_sec = time_range.get("start_sec")
    end_sec = time_range.get("end_sec")
    return f"{_format_seconds(start_sec)}초부터 {_format_seconds(end_sec)}초까지"


def _format_observed_values(observed_values: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key, value in observed_values.items():
        if isinstance(value, dict):
            stats = []
            for stat_key in ("mean", "min", "max", "count"):
                if stat_key in value:
                    stats.append(f"{stat_key}={value.get(stat_key)}")
            parts.append(f"{key}: {', '.join(stats) if stats else value}")
        elif _is_number(value):
            parts.append(f"{key}={_round(float(value))}")
        else:
            parts.append(f"{key}={value}")

    return ", ".join(parts) if parts else "없음"


def _issue_action_phrase(error: Dict[str, Any]) -> str:
    code = _error_code(error)
    name = _error_name(error)
    phrases = {
        "hip_sag": "골반이 처져",
        "hip_pike": "엉덩이가 치솟아 올라",
        "head_drop": "목이 아래로 떨어져",
        "head_rise": "머리가 위로 들려",
        "body_tilt": "몸통 라인이 기울어져",
        "elbow_deviation": "팔꿈치 각도가 기준에서 벗어나",
        "ankle_misalignment": "발목 정렬이 흐트러져",
        "unstable_body": "몸통 흔들림이 커져",
        "shoulder_collapse": "어깨 지지가 무너져",
    }
    return phrases.get(code, f"{name}이 감지되어")


def _timeline_key(errors: List[Dict[str, Any]]) -> tuple[str, tuple[str, ...]]:
    if not errors:
        return ("correct", ())
    codes = tuple(sorted({_error_code(error) for error in errors if _error_code(error)}))
    return ("needs_correction", codes)


def _build_timeline_entries(analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    windows = analysis_result.get("window_results")
    if not isinstance(windows, list):
        windows = []

    entries: List[Dict[str, Any]] = []
    for window in windows:
        if not isinstance(window, dict):
            continue

        errors = [
            error
            for error in window.get("errors", [])
            if isinstance(error, dict)
        ]
        time_range = window.get("time_range") or {}
        start_sec = time_range.get("start_sec")
        end_sec = time_range.get("end_sec")
        key = _timeline_key(errors)

        previous = entries[-1] if entries else None
        can_merge = (
            previous is not None
            and previous.get("_key") == key
            and _is_number(previous.get("end_sec"))
            and _is_number(start_sec)
            and float(start_sec) <= float(previous["end_sec"]) + 0.25
        )

        if can_merge:
            previous["end_sec"] = end_sec
            previous["time_range"] = {
                "start_sec": previous.get("start_sec"),
                "end_sec": end_sec,
            }
            previous["window_ids"].append(window.get("window_id"))
            previous["errors"].extend(errors)
            continue

        entries.append({
            "_key": key,
            "status": "needs_correction" if errors else "correct",
            "start_sec": start_sec,
            "end_sec": end_sec,
            "time_range": {
                "start_sec": start_sec,
                "end_sec": end_sec,
            },
            "window_ids": [window.get("window_id")],
            "errors": errors,
        })

    if entries:
        for entry in entries:
            entry.pop("_key", None)
        return entries

    errors = [
        error
        for error in analysis_result.get("errors", [])
        if isinstance(error, dict)
    ]
    return [
        {
            "status": "needs_correction",
            "start_sec": (error.get("time_range") or {}).get("start_sec"),
            "end_sec": (error.get("time_range") or {}).get("end_sec"),
            "time_range": error.get("time_range") or {},
            "window_ids": [error.get("window_id")],
            "errors": [error],
        }
        for error in errors
    ]


def _timeline_line(entry: Dict[str, Any]) -> str:
    time_text = _format_time_range(entry.get("time_range") or {})
    if entry.get("status") == "correct":
        return f"- {time_text}: 잘함"

    errors = [
        error
        for error in entry.get("errors", [])
        if isinstance(error, dict)
    ]
    issue_labels = list(dict.fromkeys(
        f"{_error_name(error)}({_error_code(error)})"
        for error in errors
    ))
    issue_text = ", ".join(issue_labels) or "자세 오류"
    return f"- {time_text}: 교정 필요 - {issue_text}"


def _fallback_timeline_feedback(
    timeline_entries: List[Dict[str, Any]],
    docs_by_error_code: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    feedback: List[Dict[str, Any]] = []

    for entry in timeline_entries:
        time_text = _format_time_range(entry.get("time_range") or {})
        if entry.get("status") == "correct":
            message = f"{time_text}는 자세를 잘 유지했습니다."
        else:
            errors = [
                error
                for error in entry.get("errors", [])
                if isinstance(error, dict)
            ]
            phrases = []
            coaching_snippets = []
            for error in errors:
                code = _error_code(error)
                phrases.append(_issue_action_phrase(error))
                docs = docs_by_error_code.get(code, [])
                if docs:
                    meta = docs[0].get("metadata") or {}
                    coaching_text = str(meta.get("coaching") or docs[0].get("document") or "")
                    first_tip = coaching_text.split("||")[0].strip()
                    if first_tip:
                        coaching_snippets.append(first_tip)

            issue_text = ", ".join(dict.fromkeys(phrases)) or "자세가 무너져"
            coaching_text = " ".join(dict.fromkeys(coaching_snippets))
            if coaching_text:
                message = f"{time_text}는 {issue_text} 보입니다. {coaching_text}"
            else:
                message = f"{time_text}는 {issue_text} 보입니다. 해당 구간에서 자세를 다시 정렬하세요."

        feedback.append({
            "start_sec": entry.get("start_sec"),
            "end_sec": entry.get("end_sec"),
            "status": entry.get("status"),
            "window_ids": entry.get("window_ids", []),
            "message": message,
        })

    return feedback


def _coaching_tips_for_error(
    error_code: str,
    docs_by_error_code: Dict[str, List[Dict[str, Any]]],
    limit: int = 2,
) -> List[str]:
    tips: List[str] = []

    for doc in docs_by_error_code.get(error_code, []):
        metadata = doc.get("metadata") or {}
        text = str(metadata.get("coaching") or doc.get("document") or "")
        for chunk in text.split("||"):
            tip = re.sub(r"\s+", " ", chunk).strip()
            if tip and tip not in tips:
                tips.append(tip)
            if len(tips) >= limit:
                return tips

    return tips


def _window_errors_for_evaluation(
    errors: List[Dict[str, Any]],
    docs_by_error_code: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    evaluated_errors: List[Dict[str, Any]] = []
    seen_codes: set[str] = set()

    for error in errors:
        code = _error_code(error)
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        evaluated_errors.append({
            "error_code": code,
            "error_name": _error_name(error),
            "severity": error.get("severity"),
            "action_phrase": _issue_action_phrase(error),
            "observed_values": error.get("observed_values", {}),
            "threshold_values": error.get("threshold_values", {}),
            "coaching_tips": _coaching_tips_for_error(code, docs_by_error_code),
        })

    return evaluated_errors


def _build_window_evaluations(
    analysis_result: Dict[str, Any],
    docs_by_error_code: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    windows = analysis_result.get("window_results")
    if not isinstance(windows, list):
        windows = []

    evaluations: List[Dict[str, Any]] = []
    for window in windows:
        if not isinstance(window, dict):
            continue

        errors = [
            error
            for error in window.get("errors", [])
            if isinstance(error, dict)
        ]
        time_range = window.get("time_range") or {}
        evaluated_errors = _window_errors_for_evaluation(errors, docs_by_error_code)
        status = "needs_correction" if evaluated_errors else "correct"

        evaluations.append({
            "window_id": window.get("window_id"),
            "segment_id": window.get("segment_id"),
            "status": status,
            "time_range": time_range,
            "start_sec": time_range.get("start_sec"),
            "end_sec": time_range.get("end_sec"),
            "window_ids": [window.get("window_id")],
            "errors": evaluated_errors,
            "evaluation": (
                "자세 오류가 감지되지 않았습니다."
                if status == "correct"
                else "교정이 필요한 자세 오류가 감지되었습니다."
            ),
        })

    if evaluations:
        return evaluations

    timeline_entries = _build_timeline_entries(analysis_result)
    for entry in timeline_entries:
        errors = [
            error
            for error in entry.get("errors", [])
            if isinstance(error, dict)
        ]
        evaluated_errors = _window_errors_for_evaluation(errors, docs_by_error_code)
        evaluations.append({
            "window_id": None,
            "segment_id": None,
            "status": "needs_correction" if evaluated_errors else "correct",
            "time_range": entry.get("time_range", {}),
            "start_sec": entry.get("start_sec"),
            "end_sec": entry.get("end_sec"),
            "window_ids": entry.get("window_ids", []),
            "errors": evaluated_errors,
            "evaluation": (
                "자세 오류가 감지되지 않았습니다."
                if not evaluated_errors
                else "교정이 필요한 자세 오류가 감지되었습니다."
            ),
        })

    return evaluations


def _set_feedback_summary(
    exercise: str,
    window_evaluations: List[Dict[str, Any]],
    source_error_codes: List[str],
) -> str:
    window_count = len(window_evaluations)
    correction_count = sum(
        1
        for evaluation in window_evaluations
        if evaluation.get("status") == "needs_correction"
    )

    if correction_count == 0:
        return f"{exercise} 자세가 {window_count}개 window에서 안정적으로 유지됐습니다."

    error_text = ", ".join(source_error_codes) if source_error_codes else "자세 오류"
    return f"{exercise} {window_count}개 window 중 {correction_count}개 window에서 교정이 필요합니다: {error_text}."


def _window_evaluation_prompt_line(evaluation: Dict[str, Any]) -> str:
    time_text = _format_time_range(evaluation.get("time_range") or {})
    if evaluation.get("status") == "correct":
        return f"- {time_text}: 정상, window_ids={evaluation.get('window_ids', [])}"

    error_parts = []
    for error in evaluation.get("errors", []):
        if not isinstance(error, dict):
            continue
        tips = error.get("coaching_tips") or []
        tip_text = " / ".join(str(tip) for tip in tips[:2]) if isinstance(tips, list) else ""
        error_parts.append(
            f"{error.get('error_name')}({error.get('error_code')}), "
            f"심각도={error.get('severity')}, 코칭팁={tip_text}"
        )

    return (
        f"- {time_text}: 교정 필요, window_ids={evaluation.get('window_ids', [])}, "
        f"errors={' | '.join(error_parts)}"
    )


def _fallback_feedback_text_from_evaluations(
    set_feedback: Dict[str, Any],
) -> Dict[str, Any]:
    timeline_feedback = set_feedback.get("timeline_feedback")
    if not isinstance(timeline_feedback, list):
        timeline_feedback = []

    coaching = " ".join(
        str(item.get("message"))
        for item in timeline_feedback
        if isinstance(item, dict) and item.get("message")
    )
    if not coaching:
        coaching = str(set_feedback.get("coaching") or "")

    next_action = ""
    for item in timeline_feedback:
        if isinstance(item, dict) and item.get("status") == "needs_correction":
            next_action = str(item.get("message") or "")
            break

    return {
        "summary": str(set_feedback.get("summary", "")),
        "coaching": coaching,
        "timeline_feedback": timeline_feedback,
        "next_action": next_action,
    }


def _refine_set_feedback_text(
    set_feedback: Dict[str, Any],
    exercise: str,
    camera_view: str,
) -> Dict[str, Any]:
    fallback = _fallback_feedback_text_from_evaluations(set_feedback)
    window_evaluations = set_feedback.get("window_evaluations")
    if not isinstance(window_evaluations, list) or not window_evaluations:
        return fallback

    prompt_lines = [
        _window_evaluation_prompt_line(evaluation)
        for evaluation in window_evaluations
        if isinstance(evaluation, dict)
    ]

    prompt = (
        f"당신은 운동 자세 피드백 문장을 편집하는 AI입니다.\n"
        f"아래 window별 평가와 RAG 코칭팁만 사용해서 사용자에게 보여줄 최종 문장을 작성하세요.\n"
        f"자세 판단을 새로 하지 말고, 제공된 초 구간과 오류만 사용하세요.\n\n"
        f"운동: {exercise} / 촬영방향: {camera_view}\n"
        f"초안 요약: {set_feedback.get('summary', '')}\n\n"
        f"=== window별 평가 ===\n"
        f"{chr(10).join(prompt_lines)}\n\n"
        f"=== 작성 규칙 ===\n"
        f"- coaching은 반드시 시간 순서대로 작성하세요.\n"
        f"- 문장 형식은 'n초부터 m초까지는 ...'를 사용하세요.\n"
        f"- 정상 구간은 짧게 칭찬하고, 오류 구간은 오류 상태와 코칭팁을 자연스럽게 연결하세요.\n"
        f"- 인접 window의 상태와 오류가 같으면 한 구간으로 합쳐 말해도 됩니다.\n"
        f"- 없는 시간 구간이나 새로운 오류를 만들지 마세요.\n\n"
        f"- timeline_feedback.status는 반드시 'correct' 또는 'needs_correction' 중 하나만 사용하세요.\n\n"
        f"반드시 아래 JSON 형식으로만 응답하세요:\n"
        f'{{"summary": "...", "coaching": "...", "next_action": "...", '
        f'"timeline_feedback": [{{"start_sec": 0.0, "end_sec": 1.0, "status": "needs_correction", "message": "..."}}]}}'
    )

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        raw = response.content
        if isinstance(raw, list):
            raw = "\n".join(
                part["text"] for part in raw if isinstance(part, dict) and "text" in part
            )

        json_match = re.search(r'\{[\s\S]*\}', str(raw).strip())
        if not json_match:
            return fallback

        parsed = json.loads(json_match.group())
        timeline_feedback = parsed.get("timeline_feedback")
        if not isinstance(timeline_feedback, list):
            timeline_feedback = fallback["timeline_feedback"]
        else:
            for item in timeline_feedback:
                if not isinstance(item, dict):
                    continue
                status = str(item.get("status") or "")
                if status not in {"correct", "needs_correction"}:
                    item["status"] = "needs_correction" if status else "correct"

        return {
            "summary": str(parsed.get("summary") or fallback["summary"]),
            "coaching": str(parsed.get("coaching") or fallback["coaching"]),
            "timeline_feedback": timeline_feedback,
            "next_action": str(parsed.get("next_action") or fallback["next_action"]),
        }
    except Exception:
        return fallback


def _docs_by_error_code(retrieved_docs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for doc in retrieved_docs:
        if not isinstance(doc, dict):
            continue
        code = str(doc.get("error_code") or "").strip()
        if not code:
            continue
        grouped.setdefault(code, []).append(doc)
    return grouped


def _generate_set_feedback(
    analysis_result: Dict[str, Any],
    retrieved_docs: List[Dict[str, Any]],
    exercise: str,
    camera_view: str,
) -> Dict[str, Any]:
    errors = [
        error
        for error in analysis_result.get("errors", [])
        if isinstance(error, dict)
    ]
    timeline_entries = _build_timeline_entries(analysis_result)
    docs_by_code = _docs_by_error_code(retrieved_docs)
    window_evaluations = _build_window_evaluations(analysis_result, docs_by_code)
    timeline_feedback_draft = _fallback_timeline_feedback(timeline_entries, docs_by_code)
    source_error_codes = sorted({
        _error_code(error)
        for error in errors
        if _error_code(error)
    })

    coaching_draft = " ".join(
        str(item.get("message"))
        for item in timeline_feedback_draft
        if isinstance(item, dict) and item.get("message")
    )

    return {
        "summary": _set_feedback_summary(exercise, window_evaluations, source_error_codes),
        "coaching": coaching_draft,
        "timeline": timeline_entries,
        "window_evaluations": window_evaluations,
        "timeline_feedback": timeline_feedback_draft,
        "source_error_codes": source_error_codes,
        "generation_stage": "window_evaluation",
    }


def coaching_generator_node(state: FeedbackState) -> dict:
    analysis_result = state.get("analysis_result") or {}
    exercise = str(state.get("exercise") or "운동")
    camera_view = str(state.get("camera_view") or "")

    retrieved_docs = _retrieve_coaching_docs(
        errors=analysis_result.get("errors", []),
        camera_view=camera_view,
    )

    set_feedback = _generate_set_feedback(
        analysis_result=analysis_result,
        retrieved_docs=retrieved_docs,
        exercise=exercise,
        camera_view=camera_view,
    )

    return {
        "retrieved_docs": retrieved_docs,
        "set_feedback": set_feedback,
    }

# =========================================================
# 8. Text Summarizer 노드 output
# 입력: set_feedback
# 출력: feedback_text
# 평가 노드 출력물 텍스트 정리
# =========================================================
def set_text_summarize_node(state:FeedbackState) -> dict:
    print("평가 결과 text정리 노드")
    set_feedback = state.get("set_feedback") or {}
    refined_feedback = _refine_set_feedback_text(
        set_feedback=set_feedback,
        exercise=str(state.get("exercise") or "운동"),
        camera_view=str(state.get("camera_view") or ""),
    )
    timeline_feedback = refined_feedback.get("timeline_feedback")

    return {
        "feedback_text": {
            "summary": str(refined_feedback.get("summary", "")),
            "main_issue": ", ".join(set_feedback.get("source_error_codes", [])),
            "coaching": str(refined_feedback.get("coaching", "")),
            "next_action": str(refined_feedback.get("next_action", "")),
            "timeline_feedback": timeline_feedback or [],
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
    set_feedback = state.get("set_feedback") or {}
    return {
        "final_feedback": {
            "type": "set",
            "feedback_text": state.get("feedback_text", {}),
            "timeline": set_feedback.get("timeline", []),
            "source_error_codes": set_feedback.get("source_error_codes", []),
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
# ── long_term 평가용 헬퍼 ─────────────────────────────────────────────
# 리포트 "종합 평가" — DB에 저장된 누적 피드백 텍스트를 LLM 으로 종합한다.
_LONG_TERM_VALID_TYPES = {"positive", "warning", "tip"}
_LONG_TERM_MAX_ITEMS = 60


def _long_term_llm(state: FeedbackState):
    """state.api_key(또는 환경변수)로 LLM 생성. 키 없으면 None → 노드가 빈 결과 반환.

    thinking_budget=0 으로 Gemini 2.5 의 추론(thinking) 모드를 꺼 응답 속도를 단축한다
    (8~30초 → 3~5초). 미지원 모델이면 일반 생성으로 폴백.
    """
    api_key = state.get("api_key") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    model = state.get("model") or os.getenv("GEMINI_MODEL", GEMINI_MODEL)
    try:
        return ChatGoogleGenerativeAI(
            model=model, api_key=api_key, temperature=0.4, thinking_budget=0
        )
    except Exception:  # noqa: BLE001 — thinking_budget 미지원 모델 폴백
        return ChatGoogleGenerativeAI(model=model, api_key=api_key, temperature=0.4)


def _summarize_analysis_history(analysis_results: List[Dict[str, Any]]) -> List[str]:
    """누적 analysis_result 에서 오류별 발생 빈도·심각도를 집계해 프롬프트 라인으로."""
    from collections import Counter

    total = len(analysis_results)
    error_counter: Counter = Counter()
    severity_by_error: Dict[str, List[str]] = {}

    for ar in analysis_results:
        if not isinstance(ar, dict):
            continue
        seen_in_session = set()
        for err in ar.get("errors", []):
            if not isinstance(err, dict):
                continue
            code = err.get("error_code") or err.get("issue")
            name = err.get("error_name") or err.get("description") or code
            if not code:
                continue
            key = f"{name}({code})"
            if key not in seen_in_session:  # 세션당 1회 카운트
                error_counter[key] += 1
                seen_in_session.add(key)
            sev = err.get("severity")
            if sev:
                severity_by_error.setdefault(key, []).append(str(sev))

    lines: List[str] = []
    for key, cnt in error_counter.most_common(10):
        sevs = severity_by_error.get(key, [])
        sev_txt = f", 심각도: {'/'.join(dict.fromkeys(sevs))}" if sevs else ""
        lines.append(f"- {key}: 최근 {total}개 세션 중 {cnt}회 발생{sev_txt}")
    return lines


def _build_long_term_prompt(
    feedback_texts: List[str],
    analysis_results: List[Dict[str, Any]],
    stats: Dict[str, Any],
) -> str:
    sessions_count = stats.get("sessions_count")
    avg_score = stats.get("avg_score")
    best_exercise = stats.get("best_exercise")
    avg_text = f"{avg_score:.1f}점" if isinstance(avg_score, (int, float)) else "기록 없음"
    best_text = best_exercise or "기록 없음"

    analysis_lines = _summarize_analysis_history(analysis_results)
    analysis_block = "\n".join(analysis_lines) if analysis_lines else "구조화된 자세분석 기록 없음"
    numbered = "\n".join(
        f"{i + 1}. {text}" for i, text in enumerate(feedback_texts[:_LONG_TERM_MAX_ITEMS])
    ) or "자연어 피드백 기록 없음"

    return (
        "당신은 운동 자세 코칭 전문 AI입니다.\n"
        "아래는 한 사용자의 누적 자세분석 결과와 피드백 기록입니다.\n"
        "이 기록 전체를 종합하여, 사용자의 장기적인 자세 경향·개선 추이·핵심 문제를 평가하세요.\n\n"
        "=== 누적 통계 ===\n"
        f"총 운동 횟수: {sessions_count}회\n"
        f"평균 점수: {avg_text}\n"
        f"가장 잘하는 종목: {best_text}\n\n"
        "=== 자세분석 누적 결과 (오류별 발생 빈도, 최신 세션 우선) ===\n"
        f"{analysis_block}\n\n"
        "=== 자연어 피드백 기록 (최신순) ===\n"
        f"{numbered}\n\n"
        "=== 작성 규칙 ===\n"
        "- 위 자세분석 결과의 반복 오류와 심각도를 우선 근거로 삼으세요.\n"
        "- improvement_trend: 시간에 따라 나아지는지/정체인지/악화인지 평가하세요.\n"
        "- long_term_issue: 가장 자주·심각하게 반복되는 핵심 문제 1~2가지를 짚으세요.\n"
        "- messages: 잘하는 점(positive)·개선 팁(tip)·주의할 점(warning)을 균형 있게 3~5개.\n"
        "- 각 문장은 1~2문장의 친근한 한국어로, 기록에 없는 내용은 지어내지 마세요.\n\n"
        "반드시 아래 JSON 형식으로만 응답하세요:\n"
        '{"summary": "2~3문장 종합 평가", "improvement_trend": "...", "long_term_issue": "...", '
        '"messages": [{"type": "positive", "text": "..."}, {"type": "tip", "text": "..."}]}'
    )


def _parse_long_term_json(raw: str) -> Dict[str, Any]:
    empty = {"summary": "", "improvement_trend": "", "long_term_issue": "", "messages": []}
    match = re.search(r"\{[\s\S]*\}", raw or "")
    if not match:
        return empty
    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return empty

    messages: List[Dict[str, str]] = []
    for item in parsed.get("messages", []) if isinstance(parsed.get("messages"), list) else []:
        if not isinstance(item, dict):
            continue
        msg_type = str(item.get("type") or "").strip().lower()
        text = str(item.get("text") or "").strip()
        if msg_type in _LONG_TERM_VALID_TYPES and text:
            messages.append({"type": msg_type, "text": text})
    return {
        "summary": str(parsed.get("summary") or "").strip(),
        "improvement_trend": str(parsed.get("improvement_trend") or "").strip(),
        "long_term_issue": str(parsed.get("long_term_issue") or "").strip(),
        "messages": messages,
    }


def long_term_feedback_node(state:FeedbackState) -> dict:
    print("종합운동 평가 노드")
    feedback_texts = state.get("historical_feedback_texts") or []
    analysis_results = state.get("historical_analysis_results") or []
    stats = state.get("report_stats") or {}

    llm = _long_term_llm(state)
    if llm is None or (not feedback_texts and not analysis_results):
        return {"exercise_long_term_feedback": dict(
            summary="", improvement_trend="", long_term_issue="", messages=[]
        )}

    prompt = _build_long_term_prompt(feedback_texts, analysis_results, stats)
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content
        if isinstance(raw, list):
            raw = "\n".join(p["text"] for p in raw if isinstance(p, dict) and "text" in p)
    except Exception as exc:  # noqa: BLE001 — 실패는 빈 결과로(서비스가 규칙 기반 폴백)
        return {
            "exercise_long_term_feedback": dict(
                summary="", improvement_trend="", long_term_issue="", messages=[]
            ),
            "errors": [f"long_term LLM 호출 실패: {exc}"],
        }

    return {"exercise_long_term_feedback": _parse_long_term_json(str(raw))}

def long_text_summarize_node(state:FeedbackState) -> dict:
    print("종합 평가 결과 text정리 노드")
    fb = state.get("exercise_long_term_feedback") or {}
    return {
        "feedback_text": {
            "summary": fb.get("summary", ""),
            "improvement_trend": fb.get("improvement_trend", ""),
            "long_term_issue": fb.get("long_term_issue", ""),
            "messages": fb.get("messages", []),
        }
    }

def long_review_node(state:FeedbackState) -> dict:
    print("종합 평가 결과 출력 텍스트 리뷰 노드")
    fb = state.get("exercise_long_term_feedback") or {}
    return {
        "final_feedback": {
            "type": "long_term",
            "summary": fb.get("summary", ""),
            "improvement_trend": fb.get("improvement_trend", ""),
            "long_term_issue": fb.get("long_term_issue", ""),
            "messages": fb.get("messages", []),
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

# =========================================================
# RAG 채팅 루프
# analysis_result + retrieved_docs 를 컨텍스트로 유지하며
# 터미널에서 자유롭게 질문할 수 있는 대화 인터페이스
# =========================================================
def rag_chat_loop(
    analysis_result: Dict[str, Any],
    retrieved_docs: List[Dict[str, Any]],
    exercise: str,
    camera_view: str,
) -> None:
    llm = get_llm()
    errors = analysis_result.get("errors", [])

    # ── 시스템 컨텍스트 (매 턴 공통으로 포함) ─────────────────
    error_lines = []
    for e in errors:
        obs = e.get("observed_values") or {}
        obs_str = _format_observed_values(obs) if isinstance(obs, dict) else str(obs)
        ratio_pct = (e.get("occurrence_ratio") or 0) * 100
        time_range = e.get("time_range") or {}
        time_text = f" | 구간: {_format_time_range(time_range)}" if isinstance(time_range, dict) and time_range else ""
        error_lines.append(
            f"- 오류: {e.get('error_name') or e.get('description') or e.get('issue') or e.get('error_code')} "
            f"({e.get('error_code') or e.get('issue')}) | 심각도: {e.get('severity')} "
            f"| 발생비율: {ratio_pct:.0f}%{time_text} | 관찰값: {obs_str}"
        )

    doc_blocks = [
        f"[{d['error_code']} / {d['metadata'].get('variant') or '전체'}]\n{d['document']}"
        for d in retrieved_docs
    ]
    rag_context = "\n\n".join(doc_blocks) if doc_blocks else "참고 자료 없음"

    system_context = (
        f"당신은 운동 자세 코칭 전문 AI입니다.\n"
        f"아래 분석 결과와 전문 자료를 바탕으로 사용자의 질문에 답하세요.\n\n"
        f"=== 운동 정보 ===\n"
        f"운동: {exercise} / 촬영방향: {camera_view}\n\n"
        f"=== 감지된 자세 오류 ===\n"
        f"{chr(10).join(error_lines) if error_lines else '오류 없음'}\n\n"
        f"=== RAG 참고 자료 ===\n"
        f"{rag_context}"
    )

    history: List[Any] = []

    print("\n" + "=" * 60)
    print(f"  RAG 코칭 채팅 시작 | 운동: {exercise} | 오류: {[e.get('issue') for e in errors]}")
    print("  종료하려면 'q' 또는 'quit' 입력")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n질문 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n채팅을 종료합니다.")
            break

        if user_input.lower() in ("q", "quit", "exit", "종료"):
            print("채팅을 종료합니다.")
            break
        if not user_input:
            continue

        # 컨텍스트 + 히스토리 + 현재 질문 조합
        messages = [HumanMessage(content=system_context)]
        messages.extend(history)
        messages.append(HumanMessage(content=user_input))

        response = llm.invoke(messages)

        raw = response.content
        if isinstance(raw, list):
            raw = "\n".join(
                part["text"] for part in raw if isinstance(part, dict) and "text" in part
            )

        print(f"\n코치 > {raw}")

        # 히스토리에 이번 대화 추가
        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=raw))


if __name__ == "__main__":
    # ── 모드 선택 ─────────────────────────────────────────────
    # "run"  : normalized.json → 그래프 실행 → 결과 출력
    # "chat" : analysis_result JSON 로드 → RAG 채팅
    # "both" : run 후 바로 chat으로 진입
    MODE = "run"   # ← "run" / "chat" / "both" 중 선택

    # ── run 모드 입력 ─────────────────────────────────────────
    NORMALIZED_POSE_PATH = "backend/ai/llm/test_data/norm_pike.json"
    EXERCISE = "플랭크"
    CAMERA_VIEW = "측면"
    RULE_CONFIG_PATH = "backend/ai/llm/config/plank_rule_config_mediapipe.json"
    ANALYSIS_OUTPUT_PATH = "backend/ai/llm/outputs/test_normalized_analysis.json"

    # ── chat 모드 입력 (기존 analysis_result JSON 파일 경로) ──
    # MODE = "chat" 일 때만 사용. "both"면 run 결과를 그대로 사용.
    ANALYSIS_JSON_PATH = "outputs/test_normalized_analysis.json"
    # ─────────────────────────────────────────────────────────

    analysis_result: Dict[str, Any] = {}
    retrieved_docs: List[Dict[str, Any]] = []
    exercise_name = EXERCISE
    camera_view_name = CAMERA_VIEW

    if MODE in ("run", "both"):
        initial_state = {
            "normalized_pose": NORMALIZED_POSE_PATH,
            "exercise": EXERCISE,
            "camera_view": CAMERA_VIEW,
            "rule_config_path": RULE_CONFIG_PATH,
            "analysis_output_path": ANALYSIS_OUTPUT_PATH,
        }

        print("=== 그래프 실행 시작 ===")
        result = posefit_graph.invoke(initial_state)

        analysis_result = result.get("analysis_result", {})
        retrieved_docs = result.get("retrieved_docs", [])

        print("\n=== 분석 결과 ===")
        print(f"overall_status : {analysis_result.get('overall_status')}")
        print(f"errors         : {[e.get('error_code') or e.get('issue') for e in analysis_result.get('errors', [])]}")

        print("\n=== 코칭 피드백 ===")
        set_feedback = result.get("set_feedback", {})
        feedback_text = result.get("feedback_text") or result.get("final_feedback", {}).get("feedback_text", {})
        print(f"window_evaluations : {len(set_feedback.get('window_evaluations', []))}")
        print(f"summary            : {feedback_text.get('summary')}")
        print(f"coaching           :\n{feedback_text.get('coaching')}")

        print("\n=== retrieved_docs ===")
        for doc in retrieved_docs:
            print(f"  [{doc['error_code']} / {doc['metadata'].get('variant', '전체')}]")

    if MODE == "chat":
        with open(ANALYSIS_JSON_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        analysis_result = saved.get("analysis_result", saved)
        exercise_name = analysis_result.get("exercise", EXERCISE)
        camera_view_name = analysis_result.get("camera_view", CAMERA_VIEW)
        retrieved_docs = _retrieve_coaching_docs(
            errors=analysis_result.get("errors", []),
            camera_view=camera_view_name,
        )

    if MODE in ("chat", "both"):
        rag_chat_loop(
            analysis_result=analysis_result,
            retrieved_docs=retrieved_docs,
            exercise=exercise_name,
            camera_view=camera_view_name,
        )
