"""
ViTPose 포즈 추정 클래스 (run_vitpose_v2_gpu.py 기반).

다른 파일에서 import하여 사용하는 클래스 인터페이스.
CUDA 사용 가능 시 GPU, 불가 시 CPU 자동 fallback.
"""

import json
import math
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm
from transformers import (
    AutoProcessor,
    DetrForObjectDetection,
    DetrImageProcessor,
    VitPoseForPoseEstimation,
)

COCO_KP_NAMES = [
    "nose",
    "left_eye", "right_eye",
    "left_ear", "right_ear",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
]
KP_IDX = {n: i for i, n in enumerate(COCO_KP_NAMES)}

COCO_SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6),
    (5, 7), (7, 9),
    (6, 8), (8, 10),
    (5, 11), (6, 12),
    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
]

ANGLE_DEFS = [
    ("left_elbow_angle",     5,  7,  9),
    ("right_elbow_angle",    6,  8, 10),
    ("left_shoulder_angle",  7,  5, 11),
    ("right_shoulder_angle", 8,  6, 12),
    ("left_hip_angle",       5, 11, 13),
    ("right_hip_angle",      6, 12, 14),
    ("left_knee_angle",     11, 13, 15),
    ("right_knee_angle",    12, 14, 16),
]

VIS_HIGH = 0.7
VIS_LOW  = 0.4


def _angle(a, b, c) -> float:
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-9:
        return 0.0
    return float(math.degrees(math.acos(float(np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)))))


def _compute_angles(kps_xy: np.ndarray) -> dict:
    angles = {}
    for name, ai, bi, ci in ANGLE_DEFS:
        try:
            angles[name] = round(_angle(kps_xy[ai], kps_xy[bi], kps_xy[ci]), 4)
        except Exception:
            angles[name] = None
    try:
        sc = (kps_xy[5] + kps_xy[6]) / 2
        hc = (kps_xy[11] + kps_xy[12]) / 2
        kc = (kps_xy[13] + kps_xy[14]) / 2
        angles["body_line_angle"] = round(_angle(sc, hc, kc), 4)
    except Exception:
        angles["body_line_angle"] = None
    return angles


def _confidence_flag(v: float) -> str:
    if v >= VIS_HIGH:
        return "high"
    elif v >= VIS_LOW:
        return "low"
    return "excluded"


def _normalize_person(kps_xy: np.ndarray, scores: np.ndarray) -> dict:
    xs = kps_xy[:, 0].copy()
    ys = kps_xy[:, 1].copy()

    li, ri = KP_IDX["left_hip"], KP_IDX["right_hip"]
    hip_cx = float((xs[li] + xs[ri]) / 2)
    hip_cy = float((ys[li] + ys[ri]) / 2)

    xs_c = xs - hip_cx
    ys_c = ys - hip_cy

    lsi, rsi = KP_IDX["left_shoulder"], KP_IDX["right_shoulder"]
    sc_x = float((xs_c[lsi] + xs_c[rsi]) / 2)
    sc_y = float((ys_c[lsi] + ys_c[rsi]) / 2)
    torso_length = math.sqrt(sc_x**2 + sc_y**2)
    if torso_length < 1e-6:
        torso_length = 1.0

    xs_s = xs_c / torso_length
    ys_s = ys_c / torso_length

    direction_flipped = bool(xs_s[KP_IDX["nose"]] < 0)
    if direction_flipped:
        xs_s = -xs_s

    norm_kps = {
        COCO_KP_NAMES[i]: {
            "x":               round(float(xs_s[i]), 6),
            "y":               round(float(ys_s[i]), 6),
            "score":           round(float(scores[i]), 4),
            "confidence_flag": _confidence_flag(float(scores[i])),
        }
        for i in range(17)
    }

    return {
        "norm_meta": {
            "hip_center_original_px": {"x": round(hip_cx, 3), "y": round(hip_cy, 3)},
            "torso_length_original_px": round(torso_length, 3),
            "direction_flipped": direction_flipped,
        },
        "keypoints": norm_kps,
    }


def _draw_skeleton(frame, kps_xy, scores, score_thr=0.3):
    pts = [(int(x), int(y)) for x, y in kps_xy]
    for i, (x, y) in enumerate(pts):
        if scores[i] >= score_thr:
            cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
            cv2.putText(frame, str(i), (x + 4, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
    for a, b in COCO_SKELETON:
        if scores[a] >= score_thr and scores[b] >= score_thr:
            cv2.line(frame, pts[a], pts[b], (0, 200, 255), 2)


class ViTPosePoseEstimator:
    """
    ViTPose 포즈 추정 클래스 (DETR person detector + ViTPose).

    Parameters
    ----------
    video_path  : 추정할 동영상 파일 경로 (str 또는 Path)
    output_path : 출력 파일을 저장할 디렉토리 경로 (str 또는 Path)
    save_video  : True이면 스켈레톤 오버레이 영상을 저장한다 (기본값: True)
    fps         : 초당 처리할 프레임 수. None이면 원본 FPS 전체 처리 (기본값: None)
                  예) 원본 30fps 영상에서 fps=10 이면 3프레임마다 1프레임 처리

    CUDA 사용 가능 시 GPU를 자동 선택하고, 불가 시 CPU로 fallback한다.

    사용 예시
    ---------
    from vitpose_estimator import ViTPosePoseEstimator

    estimator = ViTPosePoseEstimator(
        video_path="video/source/test.mp4",
        output_path="result/output/test",
        save_video=True,
        fps=10,   # 초당 10프레임만 처리
    )
    result = estimator.run()
    # result["raw"]        → raw pose dict
    # result["normalized"] → 정규화된 pose dict
    """

    def __init__(
        self,
        video_path: str | Path,
        output_path: str | Path,
        save_video: bool = True,
        fps: float | None = None,
    ):
        self.video_path  = Path(video_path)
        self.output_path = Path(output_path)
        self.save_video  = save_video
        self.target_fps  = fps

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  device: {self.device}")
        if self.device == "cuda":
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

        self._det_proc  = None
        self._det_model = None
        self._vit_proc  = None
        self._vit_model = None

    def _load_models(self):
        if self._det_model is not None:
            return

        print("  Loading DETR person detector…")
        self._det_proc  = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        self._det_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(self.device)
        self._det_model.eval()

        print("  Loading ViTPose…")
        self._vit_proc  = AutoProcessor.from_pretrained("usyd-community/vitpose-base-simple")
        self._vit_model = VitPoseForPoseEstimation.from_pretrained("usyd-community/vitpose-base-simple").to(self.device)
        self._vit_model.eval()

    def _detect_persons(self, pil_img, threshold=0.7) -> list:
        inputs = self._det_proc(images=pil_img, return_tensors="pt").to(self.device)
        with torch.no_grad():
            with torch.amp.autocast("cuda", enabled=(self.device == "cuda")):
                outputs = self._det_model(**inputs)
        target_sizes = torch.tensor([pil_img.size[::-1]], device=self.device)
        results = self._det_proc.post_process_object_detection(
            outputs, threshold=threshold, target_sizes=target_sizes
        )[0]
        PERSON_LABEL = 1
        return [
            box.cpu().tolist()
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"])
            if label.item() == PERSON_LABEL
        ]

    def run(self) -> dict:
        """
        포즈 추정 및 정규화를 실행한다.

        Returns
        -------
        dict
            {
              "raw": { ... },        # raw_pose 결과
              "normalized": { ... }, # 정규화 결과
              "raw_json_path": Path,
              "norm_json_path": Path,
              "video_path": Path | None,
            }
        """
        if not self.video_path.exists():
            raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {self.video_path}")

        self._load_models()
        self.output_path.mkdir(parents=True, exist_ok=True)
        stem = self.video_path.stem

        raw_json_path  = self.output_path / f"{stem}_raw.json"
        norm_json_path = self.output_path / f"{stem}_normalized.json"
        vid_out_path   = self.output_path / f"{stem}_annotated.mp4" if self.save_video else None

        cap        = cv2.VideoCapture(str(self.video_path))
        src_fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total      = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        out_fps    = self.target_fps if self.target_fps is not None else src_fps
        # 원본에서 몇 프레임마다 1프레임을 추출할지 계산
        frame_step = max(1, round(src_fps / out_fps))

        writer = None
        if self.save_video:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(vid_out_path), fourcc, out_fps, (width, height))

        raw_result = {
            "model": "vitpose",
            "video_file": self.video_path.name,
            "source_fps": src_fps,
            "output_fps": out_fps,
            "frame_step": frame_step,
            "width": width,
            "height": height,
            "frames": [],
        }
        norm_result = {
            "model": "vitpose",
            "video_file": self.video_path.name,
            "normalization": {
                "steps": ["hip_center", "torso_scale", "direction_canonical"],
                "canonical_direction": "head_right",
                "coordinate_note": "hip_centered, torso_scaled (unitless, original unit: pixel)",
                "confidence_thresholds": {"high": VIS_HIGH, "low": VIS_LOW},
            },
            "source_fps": src_fps,
            "output_fps": out_fps,
            "frame_step": frame_step,
            "width": width,
            "height": height,
            "frames": [],
        }

        t_infer_total = 0.0
        t_norm_total  = 0.0
        src_frame_id  = 0   # 원본 영상의 프레임 번호
        out_frame_id  = 0   # 실제 처리된 프레임 번호

        estimated_out = max(1, total // frame_step)
        print(f"  원본 {src_fps:.1f}fps → 처리 {out_fps:.1f}fps (step={frame_step})")
        pbar = tqdm(total=estimated_out, desc=self.video_path.name, unit="f", dynamic_ncols=True)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 지정된 step에 해당하는 프레임만 처리
            if src_frame_id % frame_step != 0:
                src_frame_id += 1
                continue

            timestamp_ms = round(src_frame_id * 1000.0 / src_fps, 2)
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            raw_frame  = {"frame_id": out_frame_id, "src_frame_id": src_frame_id,
                          "timestamp_ms": timestamp_ms,
                          "pose_detected": False, "persons": []}
            norm_frame = {"frame_id": out_frame_id, "src_frame_id": src_frame_id,
                          "timestamp_ms": timestamp_ms,
                          "pose_detected": False, "persons": []}

            t0 = time.perf_counter()
            boxes_xyxy = self._detect_persons(pil_img)

            if boxes_xyxy:
                boxes_xywh = [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in boxes_xyxy]
                inputs = self._vit_proc(images=pil_img, boxes=[boxes_xywh], return_tensors="pt").to(self.device)
                with torch.no_grad():
                    outputs = self._vit_model(**inputs)
                pose_results = self._vit_proc.post_process_pose_estimation(outputs, boxes=[boxes_xywh])[0]
            else:
                pose_results = []

            if self.device == "cuda":
                torch.cuda.synchronize()
            t_infer_total += time.perf_counter() - t0

            raw_frame["pose_detected"] = len(pose_results) > 0

            t1 = time.perf_counter()
            for person_result in pose_results:
                kps    = person_result["keypoints"].cpu().numpy()  # (17, 2)
                scores = person_result["scores"].cpu().numpy()      # (17,)

                raw_person = {
                    "keypoints": {
                        COCO_KP_NAMES[i]: {
                            "x": round(float(kps[i, 0]), 3),
                            "y": round(float(kps[i, 1]), 3),
                            "score": round(float(scores[i]), 4),
                        }
                        for i in range(17)
                    },
                    "angles": {
                        k: round(v, 4) if v is not None else None
                        for k, v in _compute_angles(kps).items()
                    },
                }
                raw_frame["persons"].append(raw_person)
                norm_frame["persons"].append(_normalize_person(kps, scores))

                if self.save_video:
                    _draw_skeleton(frame, kps, scores)

            norm_frame["pose_detected"] = len(pose_results) > 0
            t_norm_total += time.perf_counter() - t1

            raw_result["frames"].append(raw_frame)
            norm_result["frames"].append(norm_frame)

            if writer is not None:
                writer.write(frame)

            src_frame_id += 1
            out_frame_id += 1
            pbar.update(1)

        pbar.close()
        cap.release()
        if writer is not None:
            writer.release()

        raw_result["total_frames"]  = out_frame_id
        norm_result["total_frames"] = out_frame_id

        with open(raw_json_path,  "w", encoding="utf-8") as f:
            json.dump(raw_result,  f, ensure_ascii=False, indent=2)
        with open(norm_json_path, "w", encoding="utf-8") as f:
            json.dump(norm_result, f, ensure_ascii=False, indent=2)

        if out_frame_id > 0:
            fps_eff = out_frame_id / (t_infer_total + t_norm_total) if (t_infer_total + t_norm_total) > 0 else 0
            print(
                f"\n  {self.video_path.name}  처리 프레임={out_frame_id} (원본 {src_frame_id}프레임)\n"
                f"    추론 합계: {t_infer_total:.2f}s  ({t_infer_total/out_frame_id*1000:.1f} ms/f)\n"
                f"    정규화 합계: {t_norm_total:.2f}s  ({t_norm_total/out_frame_id*1000:.2f} ms/f)\n"
                f"    총 처리속도: {fps_eff:.1f} fps  |  device: {self.device}"
            )

        return {
            "raw":            raw_result,
            "normalized":     norm_result,
            "raw_json_path":  raw_json_path,
            "norm_json_path": norm_json_path,
            "video_path":     vid_out_path,
        }
