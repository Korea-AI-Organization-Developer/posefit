"""프레임 키포인트 → 34차원 벡터.

COCO-17 관절을 정해진 순서로 (x, y) 평탄화한다.
저신뢰 키포인트도 좌표 그대로 사용한다(정규화 단계에서 이미 보정됨).
누락된 관절은 (0.0, 0.0) 으로 채운다.
"""

from __future__ import annotations

from .loader import COCO_17_JOINTS, FrameSample

VECTOR_DIM = len(COCO_17_JOINTS) * 2  # 34


def frame_to_vector(sample: FrameSample) -> list[float]:
    vec: list[float] = []
    for joint in COCO_17_JOINTS:
        kp = sample.keypoints.get(joint) or {}
        vec.append(float(kp.get("x", 0.0)))
        vec.append(float(kp.get("y", 0.0)))
    return vec
