"""입력 분석 결과(analysis_result) → 오류별 검색 쿼리 파싱.

group.json.txt 형태:
    { "analysis_result": {
        "exercise": "plank", "camera_view": "side", "overall_status": "...",
        "errors": [ { "error_code": "plank_hip_sag_side_v1", "error_name": "골반 처짐",
                      "severity": "medium", "observed_values": {...}, "threshold_values": {...} } ],
        "strengths": [...] } }
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def issue_key_from_error_code(error_code: str) -> str:
    """error_code(plank_hip_sag_side_v1)에서 issue_key(hip_sag) 추출.

    조회(query)와 인덱싱(documents) 양쪽이 같은 issue_key를 만들어야
    `where={"issue_key": ...}` 메타데이터 필터가 일치한다. 그래서 한 곳에 둔다.
    """
    m = re.match(r"^plank_(.+?)_(?:side|front)_v\d+$", error_code)
    if m:
        return m.group(1)
    # fallback: 접두/접미 제거 시도
    return error_code.replace("plank_", "").replace("_side_v1", "")


@dataclass
class ErrorQuery:
    error_code: str
    error_name: str
    severity: str
    observed: dict[str, Any] = field(default_factory=dict)
    threshold: dict[str, Any] = field(default_factory=dict)

    @property
    def issue_key(self) -> str:
        """error_code(plank_hip_sag_side_v1)에서 issue_key(hip_sag) 추출."""
        return issue_key_from_error_code(self.error_code)

    def to_text(self) -> str:
        """임베딩 검색용 자연어 쿼리 문자열."""
        parts = [f"플랭크 측면 자세 오류: {self.error_name}({self.issue_key})."]
        for feature, value in self.observed.items():
            thr = self.threshold.get(feature)
            if thr is not None:
                parts.append(f"{feature} 관측 {value} (기준 {thr}).")
            else:
                parts.append(f"{feature} 관측 {value}.")
        return " ".join(parts)


def parse_analysis_result(path: str | Path) -> list[ErrorQuery]:
    """입력 JSON에서 ErrorQuery 리스트를 만든다."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    result = raw.get("analysis_result", raw)
    errors = result.get("errors", []) or []

    queries: list[ErrorQuery] = []
    for err in errors:
        queries.append(
            ErrorQuery(
                error_code=str(err.get("error_code", "")),
                error_name=str(err.get("error_name", "")),
                severity=str(err.get("severity", "")),
                observed=err.get("observed_values", {}) or {},
                threshold=err.get("threshold_values", {}) or {},
            )
        )
    return queries
