"""
pose_est.py - Pose Estimation 테스트 파이프라인

실행:
    python pose_est.py --model mediapipe
    python pose_est.py --model vitpose
    python pose_est.py --model detrpose
    python pose_est.py --model mediapipe --source video.mp4

필요 패키지:
    MediaPipe : uv add mediapipe
    ViTPose   : uv add transformers accelerate
                (torch / pillow 는 ultralytics 로 이미 설치됨)
    DETRPose  : uv add openmim
                mim install mmengine "mmcv>=2.0.0" mmdet mmpose

모델 파일 (최초 실행 시 자동 다운로드):
    ViTPose  : usyd-community/vitpose-base-simple  (~330 MB, HuggingFace)
    DETRPose : RTMDet-nano + RTMPose-s             (mmpose model zoo)
"""

import argparse
import time
from abc import ABC, abstractmethod
import os
import cv2
import numpy as np

# ── 웹캠 설정 ───────────────────────────────────────────────────
CAM_W, CAM_H, CAM_FPS = 640, 480, 30

# ── COCO-17 skeleton (ViTPose / DETRPose 공통) ──────────────────
COCO_SKELETON = [
    (0, 1),  (0, 2),  (1, 3),  (2, 4),           # 얼굴
    (5, 7),  (7, 9),  (6, 8),  (8, 10),           # 팔
    (5, 6),  (5, 11), (6, 12), (11, 12),           # 몸통
    (11, 13),(13, 15),(12, 14),(14, 16),            # 다리
]

# ── MediaPipe-33 skeleton ───────────────────────────────────────
MP_SKELETON = [
    (11, 12),(11, 13),(13, 15),(12, 14),(14, 16),  # 어깨·팔꿈치·손목
    (15, 17),(15, 19),(15, 21),(16, 18),(16, 20),(16, 22),  # 손
    (11, 23),(12, 24),(23, 24),                    # 몸통·골반
    (23, 25),(25, 27),(27, 29),(27, 31),(29, 31),  # 왼다리
    (24, 26),(26, 28),(28, 30),(28, 32),(30, 32),  # 오른다리
    (0, 1),  (1, 2),  (2, 3),  (3, 7),            # 얼굴 왼쪽
    (0, 4),  (4, 5),  (5, 6),  (6, 8),            # 얼굴 오른쪽
]


# ─────────────────────────────────────────────────────────────────
# 공통 베이스
# ─────────────────────────────────────────────────────────────────

class PoseEstimatorBase(ABC):
    """공통 인터페이스 및 시각화."""

    name:     str                       = "base"
    skeleton: list[tuple[int, int]]     = COCO_SKELETON

    @abstractmethod
    def estimate(
        self, frame: np.ndarray
    ) -> list[tuple[float, float, float]] | None:
        """키포인트 추출.

        Returns
        -------
        list of (x_pixel, y_pixel, confidence)  or  None (미검출)
        """
        ...

    # ── 라이브 루프 ──────────────────────────────────────────────
    def run(self, source: int | str = 0) -> None:
        """웹캠 / 영상 라이브 데모. q / ESC 로 종료."""
        src = int(source) if str(source).isdigit() else source
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print("[Error] 카메라/영상을 열 수 없습니다.")
            return

        cap.set(cv2.CAP_PROP_FPS,          CAM_FPS)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        print(f"[{self.name}] 실행 중  q/ESC=종료")

        fps_cnt, fps_t, fps_val = 0, time.time(), 0.0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)

            keypoints = self.estimate(frame)
            if keypoints:
                self._draw_skeleton(frame, keypoints)
                self._draw_keypoints(frame, keypoints)

            fps_cnt += 1
            if fps_cnt == 30:
                fps_val = 30.0 / max(time.time() - fps_t, 1e-6)
                fps_t, fps_cnt = time.time(), 0

            self._draw_hud(frame, fps_val, bool(keypoints))
            cv2.imshow(f"PoseEst [{self.name}]", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

        cap.release()
        cv2.destroyAllWindows()

    # ── 시각화 헬퍼 ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────
# MediaPipe Pose
# ─────────────────────────────────────────────────────────────────

class MediaPipePoseEstimator(PoseEstimatorBase):
    """Google BlazePose 기반, 33개 중 COCO-17 keypoints 만 반환 (Tasks API).

    설치: uv add mediapipe
    모델: pose_landmarker_lite.task (~4 MB, 최초 실행 시 자동 다운로드)
    """

    name     = "mediapipe"
    skeleton = COCO_SKELETON

    # MediaPipe-33 인덱스 → COCO-17 순서 매핑
    _MP_TO_COCO = [0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
    _MODEL_URL  = (
        "https://storage.googleapis.com/mediapipe-models/"
        "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    )
    _MODEL_PATH = os.path.join(os.path.dirname(__file__), "data", "pose_landmarker_lite.task")

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence:  float = 0.5,
    ):
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError:
            raise ImportError("설치 필요: uv add mediapipe")

        # 모델 파일 자동 다운로드
        if not os.path.exists(self._MODEL_PATH):
            import urllib.request
            os.makedirs(os.path.dirname(self._MODEL_PATH), exist_ok=True)
            print("[MediaPipe] pose_landmarker_lite.task 다운로드 중...")
            urllib.request.urlretrieve(self._MODEL_URL, self._MODEL_PATH)
            print("[MediaPipe] 다운로드 완료")

        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=self._MODEL_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._mp         = mp
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def estimate(self, frame: np.ndarray) -> list[tuple[float, float, float]] | None:
        h, w = frame.shape[:2]
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_img)

        if not result.pose_landmarks:
            return None

        lms = result.pose_landmarks[0]  # 첫 번째 사람
        return [
            (lms[i].x * w, lms[i].y * h, getattr(lms[i], "visibility", 1.0))
            for i in self._MP_TO_COCO
        ]


# ─────────────────────────────────────────────────────────────────
# ViTPose (HuggingFace transformers)
# ─────────────────────────────────────────────────────────────────

class ViTPoseEstimator(PoseEstimatorBase):
    """Vision Transformer 기반 COCO-17 keypoints (top-down).

    사람 검출: YOLO11n (이미 설치됨)
    포즈 추정: ViTPose-base (HuggingFace)
    설치: uv add transformers accelerate
    모델: usyd-community/vitpose-base-simple  (~330 MB, 최초 실행 시 자동 다운로드)
    """

    name     = "vitpose"
    skeleton = COCO_SKELETON

    def __init__(self, model_id: str = "usyd-community/vitpose-base-simple"):
        try:
            import torch
            from transformers import AutoImageProcessor, VitPoseForPoseEstimation
            from PIL import Image
        except ImportError:
            raise ImportError("설치 필요: uv add transformers accelerate")

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

        # Step 1: YOLO 사람 검출 → bbox 획득
        det = self._detector.predict(frame, classes=[0], conf=0.4, verbose=False)
        boxes: list[list[int]] = []
        if det and det[0].boxes is not None:
            for b in det[0].boxes:
                boxes.append(list(map(int, b.xyxy[0].tolist())))
        if not boxes:
            boxes = [[0, 0, w, h]]  # 검출 실패 시 전체 프레임을 bbox로

        # Step 2: 첫 번째 사람 crop → ViTPose
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

        kps    = results[0][0]["keypoints"].cpu().numpy()  # (17, 2)
        scores = results[0][0]["scores"].cpu().numpy()      # (17,)
        return [(float(x), float(y), float(s)) for (x, y), s in zip(kps, scores)]


# ─────────────────────────────────────────────────────────────────
# DETRPose (mmpose RTMPose)
# ─────────────────────────────────────────────────────────────────

class DETRPoseEstimator(PoseEstimatorBase):
    """DETR 계열 Transformer 기반 COCO-17 keypoints.

    RTMDet(사람 검출) + RTMPose(포즈 추정) 순차 실행.
    설치:
        uv add openmim
        mim install mmengine "mmcv>=2.0.0" mmdet mmpose
    모델: 최초 실행 시 자동 다운로드
    """

    name     = "detrpose"
    skeleton = COCO_SKELETON

    def __init__(self):
        try:
            from mmpose.apis import MMPoseInferencer
        except ImportError:
            raise ImportError(
                "설치 필요:\n"
                "  uv add openmim\n"
                "  mim install mmengine 'mmcv>=2.0.0' mmdet mmpose"
            )
        # 'human' → RTMDet-nano (검출) + RTMPose-s (포즈) 자동 로드
        self._inferencer = MMPoseInferencer("human")
        print("[DETRPose] RTMDet + RTMPose 로드 완료")

    def estimate(self, frame: np.ndarray) -> list[tuple[float, float, float]] | None:
        try:
            result = next(self._inferencer(frame, show=False, return_vis=False))
            person = result["predictions"][0][0]
            kps    = np.array(person["keypoints"])        # (17, 2)
            scores = np.array(person["keypoint_scores"])  # (17,)
            return [(float(x), float(y), float(s)) for (x, y), s in zip(kps, scores)]
        except (KeyError, IndexError, StopIteration):
            return None


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

_MODELS: dict[str, type[PoseEstimatorBase]] = {
    "mediapipe": MediaPipePoseEstimator,
    "vitpose":   ViTPoseEstimator,
    "detrpose":  DETRPoseEstimator,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pose Estimation 테스트 파이프라인",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--model",
        choices=list(_MODELS.keys()),
        default="mediapipe",
        help=(
            "사용할 모델\n"
            "  mediapipe : BlazePose 33 kp  (빠름)\n"
            "  vitpose   : ViT COCO-17 kp   (정확)\n"
            "  detrpose  : RTMPose COCO-17 kp (균형)"
        ),
    )
    parser.add_argument(
        "--source", default="0",
        help="입력 소스 (0=웹캠, 파일 경로)  [기본: 0]",
    )
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    _MODELS[args.model]().run(source)


if __name__ == "__main__":
    main()
