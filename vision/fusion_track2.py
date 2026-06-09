"""
fusion_track2.py - 얼굴 인식 + ByteTrack + Pose Estimation 융합 추적

실행:
    python fusion_track2.py --pose mediapipe
    python fusion_track2.py --pose vitpose --source video.mp4
    python fusion_track2.py --pose mediapipe --save-json out.json
    python fusion_track2.py  # pose 없이 추적만

포즈 좌표 정규화:
    타겟 bbox를 crop → estimate(crop) → (x/bbox_w, y/bbox_h) 로 정규화
    → 사람이 화면 어디에 있든 동일한 기준의 좌표 (0~1 범위)
"""

import argparse
import json

import cv2
import numpy as np

from lib.byte_tracker import ByteTrackTracker, TrackBox
from lib.face_recognizer import FaceRecognizer
from lib.pose_estimator import (
    PoseEstimatorBase,
    MediaPipePoseEstimator,
    ViTPoseEstimator,
    DETRPoseEstimator,
    compute_joint_angles,
    COCO_KP_NAMES,
    COCO_SKELETON,
)

# ── 설정 ─────────────────────────────────────────────────────────
FACE_REGION_RATIO = 0.55
DEFAULT_FACE_INTERVAL = 15

# ── 색상 (BGR) ───────────────────────────────────────────────────
C_TARGET  = (60, 220,  60)
C_SEARCH  = (100, 100, 100)
C_BLACK   = (0,   0,   0)
C_KP      = (0,  255,  80)
C_BONE    = (255, 165,  0)

_POSE_MODELS: dict[str, type[PoseEstimatorBase]] = {
    "mediapipe": MediaPipePoseEstimator,
    "vitpose":   ViTPoseEstimator,
    "detrpose":  DETRPoseEstimator,
}


class FusionTracker:
    """FaceRecognizer + ByteTrackTracker + PoseEstimator 조합 추적기.

    Parameters
    ----------
    model_name    : YOLO 추적 모델 (기본: yolo11n.pt)
    conf          : YOLO 검출 신뢰도 임계값 (기본: 0.4)
    encodings_path: encodings.bin 경로 (기본: data/encodings.bin)
    tolerance     : 얼굴 인식 임계값 (기본: 0.5)
    face_interval : SEARCHING 중 재시도 주기 프레임 수 (기본: 15)
    pose_model    : 포즈 모델 키 또는 None (기본: None)
    """

    def __init__(
        self,
        model_name: str    = "yolo11n.pt",
        conf: float        = 0.4,
        encodings_path: str | None = None,
        tolerance: float   = 0.5,
        face_interval: int = DEFAULT_FACE_INTERVAL,
        pose_model: str | None = None,
    ):
        self._tracker    = ByteTrackTracker(model_name=model_name, conf=conf, classes=[0])
        recog_kwargs     = {"tolerance": tolerance}
        if encodings_path:
            recog_kwargs["encodings_path"] = encodings_path
        self._recognizer = FaceRecognizer(**recog_kwargs)
        self.face_interval = face_interval

        self._estimator: PoseEstimatorBase | None = None
        if pose_model:
            print(f"[FusionTracker2] 포즈 모델 로드: {pose_model}")
            self._estimator = _POSE_MODELS[pose_model]()

        self._target_id:   int | None = None
        self._target_name: str | None = None
        self._seen_ids:    set[int]   = set()
        self._frame_idx = 0

    def run(self, source: int | str = 0, save_json: str | None = None) -> None:
        """추적 루프 실행. q / ESC 로 종료."""
        print(f"[FusionTracker2] source={source}  pose={self._estimator and self._estimator.name}  q/ESC=종료")
        print("[FusionTracker2] SEARCHING — 등록된 얼굴이 인식되면 추적을 시작합니다.\n")

        records: list[dict] = []

        for frame, boxes in self._tracker.stream(source):
            active_ids: set[int] = set()
            retry_tick = (self._frame_idx % self.face_interval == 0)

            for box in boxes:
                active_ids.add(box.id)

                # ── TRACKING ────────────────────────────────────
                if self._target_id is not None:
                    if box.id == self._target_id:
                        self._draw_box(frame, box, f"ID:{box.id}  {self._target_name}", C_TARGET)

                        # 포즈 추정: bbox crop → estimate → 정규화
                        if self._estimator is not None:
                            norm_kps, raw_kps = self._estimate_on_box(frame, box)
                            if raw_kps:
                                self._draw_pose(frame, raw_kps, box)
                            if save_json:
                                records.append(self._make_record(
                                    self._frame_idx, box, norm_kps
                                ))
                    continue

                # ── SEARCHING ───────────────────────────────────
                if box.id not in self._seen_ids or retry_tick:
                    self._seen_ids.add(box.id)
                    name = self._try_recognize(frame, box)
                    if name:
                        self._target_id   = box.id
                        self._target_name = name
                        print(f"[FusionTracker2] LOCKED → ID:{box.id}  '{name}'")
                        self._draw_box(frame, box, f"ID:{box.id}  {name}", C_TARGET)
                        continue

                cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), C_SEARCH, 1)

            # ── 타겟 소멸 → SEARCHING 재전환 ────────────────────
            if self._target_id is not None and self._target_id not in active_ids:
                print(f"[FusionTracker2] LOST → '{self._target_name}'  SEARCHING 재시작")
                self._target_id   = None
                self._target_name = None
                self._seen_ids.clear()

            self._frame_idx += 1
            self._draw_hud(frame)
            cv2.imshow("Fusion Tracker 2", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

        cv2.destroyAllWindows()

        if save_json and records:
            with open(save_json, "w", encoding="utf-8") as f:
                json.dump({"source": str(source), "frames": records}, f,
                          ensure_ascii=False, indent=2)
            print(f"[FusionTracker2] {len(records)}프레임 저장 완료 → {save_json}")

    # ── 포즈 추정 ────────────────────────────────────────────────

    def _estimate_on_box(
        self, frame: np.ndarray, box: TrackBox
    ) -> tuple[list | None, list | None]:
        """bbox crop으로 포즈 추정.

        Returns
        -------
        norm_kps : [(x_norm, y_norm, conf), ...] — bbox 내 정규화 좌표 (0~1)
        raw_kps  : [(x_pixel, y_pixel, conf), ...] — crop 내 pixel 좌표 (시각화용)
        """
        crop = frame[box.y1:box.y2, box.x1:box.x2]
        if crop.size == 0:
            return None, None

        raw_kps = self._estimator.estimate(crop)
        if raw_kps is None:
            return None, None

        bw = max(box.x2 - box.x1, 1)
        bh = max(box.y2 - box.y1, 1)
        norm_kps = [(x / bw, y / bh, c) for x, y, c in raw_kps]
        return norm_kps, raw_kps

    def _draw_pose(
        self,
        frame: np.ndarray,
        raw_kps: list[tuple[float, float, float]],
        box: TrackBox,
        conf_thr: float = 0.3,
    ) -> None:
        """crop 기준 raw_kps를 full frame 좌표로 변환 후 스켈레톤 그리기."""
        ox, oy = box.x1, box.y1  # bbox offset

        # 스켈레톤
        for i, j in COCO_SKELETON:
            if i >= len(raw_kps) or j >= len(raw_kps):
                continue
            xi, yi, ci = raw_kps[i]
            xj, yj, cj = raw_kps[j]
            if ci < conf_thr or cj < conf_thr:
                continue
            cv2.line(frame,
                     (int(xi) + ox, int(yi) + oy),
                     (int(xj) + ox, int(yj) + oy),
                     C_BONE, 2, cv2.LINE_AA)

        # 키포인트
        for x, y, conf in raw_kps:
            if conf < conf_thr:
                continue
            cx, cy = int(x) + ox, int(y) + oy
            cv2.circle(frame, (cx, cy), 5, C_BLACK, -1)
            cv2.circle(frame, (cx, cy), 4, C_KP,    -1)

    # ── 얼굴 인식 ────────────────────────────────────────────────

    def _try_recognize(self, frame: np.ndarray, box: TrackBox) -> str | None:
        face_y2 = box.y1 + int((box.y2 - box.y1) * FACE_REGION_RATIO)
        crop    = frame[box.y1:face_y2, box.x1:box.x2]
        return self._recognizer.recognize_crop(crop)

    # ── JSON 레코드 생성 ─────────────────────────────────────────

    @staticmethod
    def _make_record(
        frame_idx: int,
        box: TrackBox,
        norm_kps: list[tuple[float, float, float]] | None,
    ) -> dict:
        """정규화된 키포인트 + 관절 각도를 딕셔너리로 반환."""
        kps_data = []
        angles   = {}
        if norm_kps:
            kps_data = [
                {
                    "id": i,
                    "name": COCO_KP_NAMES[i] if i < len(COCO_KP_NAMES) else str(i),
                    "x_norm": round(x, 4),
                    "y_norm": round(y, 4),
                    "confidence": round(c, 4),
                }
                for i, (x, y, c) in enumerate(norm_kps)
            ]
            angles = compute_joint_angles(norm_kps)

        return {
            "frame": frame_idx,
            "bbox": {"x1": box.x1, "y1": box.y1, "x2": box.x2, "y2": box.y2},
            "keypoints": kps_data,
            "joint_angles": angles,
        }

    # ── UI 헬퍼 ─────────────────────────────────────────────────

    def _draw_hud(self, frame: np.ndarray) -> None:
        if self._target_id is None:
            msg, color = "SEARCHING...", C_SEARCH
        else:
            pose_name = self._estimator.name if self._estimator else "no pose"
            msg   = f"TRACKING  '{self._target_name}'  [{pose_name}]"
            color = C_TARGET
        cv2.putText(frame, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, C_BLACK, 3, cv2.LINE_AA)
        cv2.putText(frame, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color,   2, cv2.LINE_AA)

    @staticmethod
    def _draw_box(
        frame: np.ndarray,
        box: TrackBox,
        label: str,
        color: tuple[int, int, int],
    ) -> None:
        cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), color, 2)
        lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0]
        cv2.rectangle(frame, (box.x1, box.y1 - lh - 8), (box.x1 + lw + 6, box.y1), color, -1)
        cv2.putText(frame, label, (box.x1 + 3, box.y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_BLACK, 1, cv2.LINE_AA)


# ── CLI ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="얼굴 인식 + ByteTrack + Pose Estimation 융합 추적"
    )
    parser.add_argument("--source", default="0",
                        help="입력 소스 (0=웹캠, 파일 경로)  [기본: 0]")
    parser.add_argument("--conf", type=float, default=0.4,
                        help="YOLO 검출 신뢰도 임계값  [기본: 0.4]")
    parser.add_argument("--model", default="yolo11n.pt",
                        help="YOLO 추적 모델  [기본: yolo11n.pt]")
    parser.add_argument("--tolerance", type=float, default=0.5,
                        help="얼굴 인식 임계값  [기본: 0.5]")
    parser.add_argument("--face-interval", type=int, default=DEFAULT_FACE_INTERVAL,
                        help=f"SEARCHING 중 재시도 주기 (프레임)  [기본: {DEFAULT_FACE_INTERVAL}]")
    parser.add_argument("--encodings", default=None, metavar="PATH",
                        help="encodings.bin 경로  [기본: data/encodings.bin]")
    parser.add_argument("--pose", default=None, choices=list(_POSE_MODELS.keys()),
                        help="포즈 추정 모델 (없으면 포즈 생략)")
    parser.add_argument("--save-json", default=None, metavar="PATH",
                        help="정규화된 키포인트 저장 경로 (--pose 필요)")
    args = parser.parse_args()

    if args.save_json and not args.pose:
        parser.error("--save-json 은 --pose 와 함께 사용해야 합니다.")

    source = int(args.source) if args.source.isdigit() else args.source
    FusionTracker(
        model_name    = args.model,
        conf          = args.conf,
        encodings_path= args.encodings,
        tolerance     = args.tolerance,
        face_interval = args.face_interval,
        pose_model    = args.pose,
    ).run(source, save_json=args.save_json)


if __name__ == "__main__":
    main()
