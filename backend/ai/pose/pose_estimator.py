from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime

import cv2
import numpy as np

CAM_W, CAM_H, CAM_FPS = 640, 480, 30

COCO_KP_NAMES: list[str] = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]

JOINT_ANGLE_DEFS: dict[str, tuple[int, int, int]] = {
    "left_elbow":     (5,  7,  9),
    "right_elbow":    (6,  8, 10),
    "left_shoulder":  (7,  5, 11),
    "right_shoulder": (8,  6, 12),
    "left_hip":       (5, 11, 13),
    "right_hip":      (6, 12, 14),
    "left_knee":      (11, 13, 15),
    "right_knee":     (12, 14, 16),
}

COCO_SKELETON: list[tuple[int, int]] = [
    (0, 1),  (0, 2),  (1, 3),  (2, 4),
    (5, 7),  (7, 9),  (6, 8),  (8, 10),
    (5, 6),  (5, 11), (6, 12), (11, 12),
    (11, 13),(13, 15),(12, 14),(14, 16),
]

MP_SKELETON: list[tuple[int, int]] = [
    (11, 12),(11, 13),(13, 15),(12, 14),(14, 16),
    (15, 17),(15, 19),(15, 21),(16, 18),(16, 20),(16, 22),
    (11, 23),(12, 24),(23, 24),
    (23, 25),(25, 27),(27, 29),(27, 31),(29, 31),
    (24, 26),(26, 28),(28, 30),(28, 32),(30, 32),
    (0, 1),  (1, 2),  (2, 3),  (3, 7),
    (0, 4),  (4, 5),  (5, 6),  (6, 8),
]

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)


def compute_joint_angles(
    keypoints: list[tuple[float, float, float]],
    conf_thr: float = 0.0,
) -> dict[str, float | None]:
    """각 관절의 각도(도)를 반환. 신뢰도 미달 키포인트는 None."""
    angles: dict[str, float | None] = {}
    for name, (ia, iv, ib) in JOINT_ANGLE_DEFS.items():
        xa, ya, ca  = keypoints[ia]
        xv, yv, cv_ = keypoints[iv]
        xb, yb, cb  = keypoints[ib]
        if ca < conf_thr or cv_ < conf_thr or cb < conf_thr:
            angles[name] = None
            continue
        va   = np.array([xa - xv, ya - yv], dtype=float)
        vb   = np.array([xb - xv, yb - yv], dtype=float)
        norm = np.linalg.norm(va) * np.linalg.norm(vb)
        if norm < 1e-6:
            angles[name] = None
            continue
        cos_a = np.clip(np.dot(va, vb) / norm, -1.0, 1.0)
        angles[name] = round(float(np.degrees(np.arccos(cos_a))), 2)
    return angles


class PoseEstimatorBase(ABC):
    """공통 인터페이스 및 시각화."""

    name:     str                   = "base"
    skeleton: list[tuple[int, int]] = COCO_SKELETON

    @abstractmethod
    def estimate(
        self, frame: np.ndarray
    ) -> list[tuple[float, float, float]] | None:
        """키포인트 추출.

        Returns
        -------
        list of (x_pixel, y_pixel, confidence) × 17  or  None (미검출)
        """
        ...

    def run(
        self,
        source: int | str = 0,
        angle_conf_thr: float = 0.0,
    ) -> None:
        """웹캠 / 영상 라이브 데모. q / ESC 로 종료. JSON 자동 저장."""
        src      = int(source) if str(source).isdigit() else source
        out_path = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print("[Error] 카메라/영상을 열 수 없습니다.")
            return

        cap.set(cv2.CAP_PROP_FPS,          CAM_FPS)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        print(f"[{self.name}] 실행 중  q/ESC=종료  저장={out_path}")

        fps_cnt, fps_t, fps_val = 0, time.time(), 0.0
        frame_idx = 0
        records: list[dict] = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)

            keypoints = self.estimate(frame)
            if keypoints:
                self._draw_skeleton(frame, keypoints)
                self._draw_keypoints(frame, keypoints)

            records.append({
                "frame": frame_idx,
                "keypoints": [
                    {
                        "id": i,
                        "name": COCO_KP_NAMES[i] if i < len(COCO_KP_NAMES) else str(i),
                        "x": round(x, 2), "y": round(y, 2),
                        "confidence": round(c, 4),
                    }
                    for i, (x, y, c) in enumerate(keypoints)
                ] if keypoints else [],
                "joint_angles": compute_joint_angles(keypoints, angle_conf_thr) if keypoints else {},
            })

            fps_cnt += 1
            frame_idx += 1
            if fps_cnt == 30:
                fps_val = 30.0 / max(time.time() - fps_t, 1e-6)
                fps_t, fps_cnt = time.time(), 0

            self._draw_hud(frame, fps_val, bool(keypoints))
            cv2.imshow(f"PoseEst [{self.name}]", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

        cap.release()
        cv2.destroyAllWindows()

        data = {"model": self.name, "source": str(source), "frames": records}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[{self.name}] {len(records)}프레임 저장 완료 → {out_path}")

    def _draw_keypoints(
        self,
        frame: np.ndarray,
        keypoints: list[tuple[float, float, float]],
        conf_thr: float = 0.3,
    ) -> None:
        for x, y, conf in keypoints:
            if conf < conf_thr:
                continue
            cv2.circle(frame, (int(x), int(y)), 5, (0,   0,   0), -1)
            cv2.circle(frame, (int(x), int(y)), 4, (0, 255,  80), -1)

    def _draw_skeleton(
        self,
        frame: np.ndarray,
        keypoints: list[tuple[float, float, float]],
        conf_thr: float = 0.3,
    ) -> None:
        for i, j in self.skeleton:
            if i >= len(keypoints) or j >= len(keypoints):
                continue
            xi, yi, ci = keypoints[i]
            xj, yj, cj = keypoints[j]
            if ci < conf_thr or cj < conf_thr:
                continue
            cv2.line(frame, (int(xi), int(yi)), (int(xj), int(yj)),
                     (255, 165, 0), 2, cv2.LINE_AA)

    def _draw_hud(self, frame: np.ndarray, fps: float, detected: bool) -> None:
        status = "DETECTED" if detected else "no person"
        label  = f"[{self.name}]  {fps:.1f} fps  {status}"
        cv2.putText(frame, label, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0),     3, cv2.LINE_AA)
        cv2.putText(frame, label, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)


class MediaPipePoseEstimator(PoseEstimatorBase):
    """Google BlazePose 기반, COCO-17 keypoints 반환 (Tasks API).

    Parameters
    ----------
    model_path : str | None
        pose_landmarker_lite.task 경로. None 이면 ./data/ 에 자동 다운로드.
    """

    name     = "mediapipe"
    skeleton = COCO_SKELETON

    _MP_TO_COCO = [0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence:  float = 0.5,
        model_path: str | None = None,
    ):
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError:
            raise ImportError("설치 필요: pip install mediapipe")

        if model_path is None:
            model_path = os.path.join(os.getcwd(), "data", "pose_landmarker_lite.task")

        if not os.path.exists(model_path):
            import urllib.request
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            print("[MediaPipe] pose_landmarker_lite.task 다운로드 중...")
            urllib.request.urlretrieve(_MODEL_URL, model_path)
            print("[MediaPipe] 다운로드 완료")

        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._mp         = mp
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def estimate(self, frame: np.ndarray) -> list[tuple[float, float, float]] | None:
        h, w   = frame.shape[:2]
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_img)

        if not result.pose_landmarks:
            return None

        lms = result.pose_landmarks[0]
        return [
            (lms[i].x * w, lms[i].y * h, getattr(lms[i], "visibility", 1.0))
            for i in self._MP_TO_COCO
        ]


class ViTPoseEstimator(PoseEstimatorBase):
    """Vision Transformer 기반 COCO-17 keypoints (top-down).

    사람 검출: YOLO11n  /  포즈 추정: ViTPose-base (HuggingFace)
    설치: pip install transformers accelerate ultralytics
    """

    name     = "vitpose"
    skeleton = COCO_SKELETON

    def __init__(self, model_id: str = "usyd-community/vitpose-base-simple"):
        try:
            import torch
            from transformers import AutoImageProcessor, VitPoseForPoseEstimation
            from PIL import Image
        except ImportError:
            raise ImportError("설치 필요: pip install transformers accelerate")

        from ultralytics import YOLO

        self._torch     = torch
        self._Image     = Image
        self._device    = "cuda" if torch.cuda.is_available() else "cpu"
        self._detector  = YOLO("yolo11n.pt")
        self._processor = AutoImageProcessor.from_pretrained(model_id)
        self._model     = VitPoseForPoseEstimation.from_pretrained(model_id)
        self._model.eval().to(self._device)
        print(f"[ViTPose] device={self._device}  model={model_id}")

    def estimate(self, frame: np.ndarray) -> list[tuple[float, float, float]] | None:
        h, w = frame.shape[:2]

        det = self._detector.predict(frame, classes=[0], conf=0.4, verbose=False)
        boxes: list[list[int]] = []
        if det and det[0].boxes is not None:
            for b in det[0].boxes:
                boxes.append(list(map(int, b.xyxy[0].tolist())))
        if not boxes:
            boxes = [[0, 0, w, h]]

        image  = self._Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        inputs = self._processor(image, boxes=[boxes[:1]], return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with self._torch.no_grad():
            outputs = self._model(**inputs)

        results = self._processor.post_process_pose_estimation(
            outputs, boxes=[boxes[:1]]
        )
        if not results or not results[0]:
            return None

        kps    = results[0][0]["keypoints"].cpu().numpy()
        scores = results[0][0]["scores"].cpu().numpy()
        return [(float(x), float(y), float(s)) for (x, y), s in zip(kps, scores)]


class DETRPoseEstimator(PoseEstimatorBase):
    """RTMDet(사람 검출) + RTMPose(포즈) — mmpose 기반.

    설치: pip install openmim
          mim install mmengine "mmcv==2.1.0" mmdet mmpose
    """

    name     = "detrpose"
    skeleton = COCO_SKELETON

    def __init__(self):
        try:
            from mmpose.apis import MMPoseInferencer
        except ImportError:
            raise ImportError(
                "설치 필요:\n"
                "  pip install openmim\n"
                "  mim install mmengine 'mmcv==2.1.0' mmdet mmpose"
            )
        self._inferencer = MMPoseInferencer("human")
        print("[DETRPose] RTMDet + RTMPose 로드 완료")

    def estimate(self, frame: np.ndarray) -> list[tuple[float, float, float]] | None:
        try:
            result = next(self._inferencer(frame, show=False, return_vis=False))
            person = result["predictions"][0][0]
            kps    = np.array(person["keypoints"])
            scores = np.array(person["keypoint_scores"])
            return [(float(x), float(y), float(s)) for (x, y), s in zip(kps, scores)]
        except (KeyError, IndexError, StopIteration):
            return None
