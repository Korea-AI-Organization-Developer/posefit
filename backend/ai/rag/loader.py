"""정규화된 ViTPose JSON 로더.

`data/result/output/vitpose_normalized/{answer,wrong}/*.json` 형식을 가정한다.
좌표는 이미 hip-centered + torso-scaled + direction-canonical 이므로
추가 정규화 없이 그대로 사용한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

COCO_17_JOINTS: tuple[str, ...] = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)


@dataclass(frozen=True)
class FrameSample:
    video_file: str
    label: str  # "correct" | "wrong"
    frame_id: int
    timestamp_ms: float
    keypoints: dict[str, dict[str, float]]


def _label_from_filename(path: Path) -> str:
    # answer/ 폴더라도 plank_false_*.json 이면 wrong, wrong/ 폴더의 plank_true_13.json 은 correct.
    name = path.stem.lower()
    if "false" in name:
        return "wrong"
    if "true" in name:
        return "correct"
    # 폴더 fallback
    return "correct" if path.parent.name == "answer" else "wrong"


def iter_frames(json_path: Path) -> Iterator[FrameSample]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    video_file = data.get("video_file", json_path.name)
    label = _label_from_filename(json_path)

    for frame in data.get("frames", []):
        if not frame.get("pose_detected"):
            continue
        persons = frame.get("persons") or []
        if not persons:
            continue
        kp = persons[0].get("keypoints") or {}
        if not kp:
            continue
        yield FrameSample(
            video_file=video_file,
            label=label,
            frame_id=int(frame["frame_id"]),
            timestamp_ms=float(frame["timestamp_ms"]),
            keypoints=kp,
        )


def iter_dataset(root: Path) -> Iterator[FrameSample]:
    """root 아래 answer/, wrong/ 의 모든 JSON을 프레임 단위로 순회한다."""
    for sub in ("answer", "wrong"):
        sub_dir = root / sub
        if not sub_dir.exists():
            continue
        for json_path in sorted(sub_dir.glob("*.json")):
            yield from iter_frames(json_path)
