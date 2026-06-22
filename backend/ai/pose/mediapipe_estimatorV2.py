"""
MediaPipe 포즈 추정 함수/클래스 (run_mediapipe_v2_gpu.py 기반).

다른 파일에서 import하여 사용하는 함수 및 클래스 인터페이스.
GPU delegate(OpenGL) 우선 시도, 실패 시 CPU 자동 fallback.
"""

import json
import math
import re
import time
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

import cv2
import mediapipe as mp
import numpy as np

MODEL_DIR  = Path(__file__).parent / "models"
MODEL_NAME = "pose_landmarker_heavy.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_heavy/float16/latest/"
    "pose_landmarker_heavy.task"
)

BaseOptions        = mp.tasks.BaseOptions
PoseLandmarker     = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOpts = mp.tasks.vision.PoseLandmarkerOptions
RunningMode        = mp.tasks.vision.RunningMode

MP_TO_COCO = [0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]

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
DEFAULT_OUTPUT_ROOT = Path(r"C:\posefit_saves")
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _stringify_value(value) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _safe_path_part(value) -> str:
    text = _stringify_value(value).strip()
    text = INVALID_FILENAME_CHARS.sub("-", text)
    text = re.sub(r"\s+", "_", text).strip(". ")
    if not text:
        raise ValueError("user_id, exercise_id, start_at 값은 비어 있을 수 없습니다.")
    return text


def _json_ready_metadata(metadata: dict | None) -> dict:
    if not metadata:
        return {}
    return {str(key): _stringify_value(value) for key, value in metadata.items()}


def _resolve_video_path(video_url: str | Path, upload_root: str | Path | None = None) -> Path:
    video_text = str(video_url)
    direct_path = Path(video_text)
    if direct_path.exists() or direct_path.drive:
        return direct_path

    parsed = urlparse(video_text)
    if parsed.scheme in {"http", "https", "file"}:
        video_text = unquote(parsed.path)

    relative_path = video_text.lstrip("/\\")
    base_dir = Path(upload_root) if upload_root is not None else Path.cwd()
    return base_dir / relative_path


def _build_pose_point_json_path(
    user_id,
    exercise_id,
    start_at,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> Path:
    safe_user_id = _safe_path_part(user_id)
    safe_exercise_id = _safe_path_part(exercise_id)
    safe_start_at = _safe_path_part(start_at)
    filename = f"{safe_user_id}_{safe_exercise_id}_{safe_start_at}.json"
    return Path(output_root) / safe_user_id / safe_exercise_id / "pose_point" / filename


def _download_model() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dest = MODEL_DIR / MODEL_NAME
    if not dest.exists():
        print(f"  모델 다운로드 중: {MODEL_NAME} …")
        urllib.request.urlretrieve(MODEL_URL, dest)
        print(f"  저장 완료 → {dest}")
    return dest


def _angle(a, b, c) -> float:
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-9:
        return 0.0
    return float(math.degrees(math.acos(float(np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)))))


def _compute_angles(coco_pts: list) -> dict:
    angles = {}
    for name, ai, bi, ci in ANGLE_DEFS:
        try:
            angles[name] = round(_angle(coco_pts[ai][:3], coco_pts[bi][:3], coco_pts[ci][:3]), 4)
        except Exception:
            angles[name] = None
    try:
        sc = [(coco_pts[5][k] + coco_pts[6][k]) / 2 for k in range(3)]
        hc = [(coco_pts[11][k] + coco_pts[12][k]) / 2 for k in range(3)]
        kc = [(coco_pts[13][k] + coco_pts[14][k]) / 2 for k in range(3)]
        angles["body_line_angle"] = round(_angle(sc, hc, kc), 4)
    except Exception:
        angles["body_line_angle"] = None
    try:
        sc = [(coco_pts[5][k] + coco_pts[6][k]) / 2 for k in range(3)]
        hc = [(coco_pts[11][k] + coco_pts[12][k]) / 2 for k in range(3)]
        angles["trunk_lean_angle"] = round(_angle(coco_pts[0][:3], sc, hc), 4)
    except Exception:
        angles["trunk_lean_angle"] = None
    return angles


def _extract_coco_keypoints(mp33_landmarks) -> list:
    return [
        [
            mp33_landmarks[mp_idx].x,
            mp33_landmarks[mp_idx].y,
            mp33_landmarks[mp_idx].z,
            mp33_landmarks[mp_idx].visibility,
            mp33_landmarks[mp_idx].presence,
        ]
        for mp_idx in MP_TO_COCO
    ]


def _confidence_flag(v: float) -> str:
    if v >= VIS_HIGH:
        return "high"
    elif v >= VIS_LOW:
        return "low"
    return "excluded"


def _normalize_person(coco_pts: list) -> dict:
    xs  = np.array([p[0] for p in coco_pts])
    ys  = np.array([p[1] for p in coco_pts])
    zs  = np.array([p[2] for p in coco_pts])
    vis = [p[3] for p in coco_pts]
    pre = [p[4] for p in coco_pts]

    li, ri = KP_IDX["left_hip"], KP_IDX["right_hip"]
    hip_cx = float((xs[li] + xs[ri]) / 2)
    hip_cy = float((ys[li] + ys[ri]) / 2)
    hip_cz = float((zs[li] + zs[ri]) / 2)

    xs_c = xs - hip_cx
    ys_c = ys - hip_cy
    zs_c = zs - hip_cz

    lsi, rsi = KP_IDX["left_shoulder"], KP_IDX["right_shoulder"]
    sc_x = float((xs_c[lsi] + xs_c[rsi]) / 2)
    sc_y = float((ys_c[lsi] + ys_c[rsi]) / 2)
    sc_z = float((zs_c[lsi] + zs_c[rsi]) / 2)
    torso_length = math.sqrt(sc_x**2 + sc_y**2 + sc_z**2)
    if torso_length < 1e-6:
        torso_length = 1.0

    xs_s = xs_c / torso_length
    ys_s = ys_c / torso_length
    zs_s = zs_c / torso_length

    direction_flipped = bool(xs_s[KP_IDX["nose"]] < 0)
    if direction_flipped:
        xs_s = -xs_s

    norm_kps = {
        COCO_KP_NAMES[i]: {
            "x":               round(float(xs_s[i]), 6),
            "y":               round(float(ys_s[i]), 6),
            "z":               round(float(zs_s[i]), 6),
            "visibility":      vis[i],
            "presence":        pre[i],
            "confidence_flag": _confidence_flag(vis[i]),
        }
        for i in range(17)
    }

    return {
        "norm_meta": {
            "hip_center_original": {"x": round(hip_cx, 6), "y": round(hip_cy, 6), "z": round(hip_cz, 6)},
            "torso_length_original": round(torso_length, 6),
            "direction_flipped": direction_flipped,
        },
        "keypoints": norm_kps,
    }


def _draw_coco_skeleton(frame: np.ndarray, coco_pts: list, vis_thr: float = 0.5):
    h, w = frame.shape[:2]
    px  = [(int(p[0] * w), int(p[1] * h)) for p in coco_pts]
    vis = [p[3] for p in coco_pts]
    for i, (x, y) in enumerate(px):
        if vis[i] >= vis_thr:
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(frame, str(i), (x + 4, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
    for a, b in COCO_SKELETON:
        if vis[a] >= vis_thr and vis[b] >= vis_thr:
            cv2.line(frame, px[a], px[b], (0, 200, 255), 2)


def _build_options(model_path: Path, use_gpu: bool) -> PoseLandmarkerOpts:
    delegate = BaseOptions.Delegate.GPU if use_gpu else BaseOptions.Delegate.CPU
    return PoseLandmarkerOpts(
        base_options=BaseOptions(model_asset_path=str(model_path), delegate=delegate),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )


class MediaPipePoseEstimator:
    """
    MediaPipe 포즈 추정 클래스.

    Parameters
    ----------
    video_path  : 추정할 동영상 파일 경로 (str 또는 Path)
    output_path : 출력 파일을 저장할 디렉토리 경로 (str 또는 Path)
    save_video  : True이면 스켈레톤 오버레이 영상을 저장한다 (기본값: False)
    fps         : 초당 처리할 프레임 수. None이면 원본 FPS 전체 처리 (기본값: None)
                  예) 원본 30fps 영상에서 fps=10 이면 3프레임마다 1프레임 처리

    사용 예시
    ---------
    from mediapipe_estimator import MediaPipePoseEstimator

    estimator = MediaPipePoseEstimator(
        video_path="video/source/test.mp4",
        output_path="result/output/test",
        save_video=False,
        fps=10,   # 초당 10프레임만 처리
    )
    result = estimator.run()
    # result["normalized"] → 정규화된 pose dict
    """

    def __init__(
        self,
        video_path: str | Path,
        output_path: str | Path,
        save_video: bool = False,
        fps: float | None = None,
        output_json_path: str | Path | None = None,
        metadata: dict | None = None,
    ):
        self.video_path  = Path(video_path)
        self.output_path = Path(output_path)
        self.save_video  = save_video
        self.target_fps  = fps
        self.output_json_path = Path(output_json_path) if output_json_path is not None else None
        self.metadata = _json_ready_metadata(metadata)

        self._model_path = _download_model()
        self._use_gpu    = self._detect_gpu()

    def _detect_gpu(self) -> bool:
        print("  GPU delegate 테스트 중…")
        try:
            opts = _build_options(self._model_path, use_gpu=True)
            with PoseLandmarker.create_from_options(opts):
                pass
            print("  GPU delegate: 사용 가능")
            return True
        except Exception as e:
            print(f"  GPU delegate 불가 ({e.__class__.__name__}), CPU fallback")
            return False

    def run(self) -> dict:
        """
        포즈 추정 및 정규화를 실행한다.

        Returns
        -------
        dict
            {
              "normalized": { ... }, # 정규화 결과
              "norm_json_path": Path,
              "video_path": Path | None,
            }
        """
        if not self.video_path.exists():
            raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {self.video_path}")

        self.output_path.mkdir(parents=True, exist_ok=True)
        stem = self.video_path.stem

        video_out_dir = self.output_path / stem
        if self.output_json_path is not None:
            norm_json_path = self.output_json_path
            video_out_dir = norm_json_path.parent
        else:
            norm_json_path = video_out_dir / "normalized.json"
        video_out_dir.mkdir(parents=True, exist_ok=True)
        vid_out_path   = video_out_dir / "annotated.mp4" if self.save_video else None

        cap         = cv2.VideoCapture(str(self.video_path))
        src_fps     = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total       = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        out_fps     = self.target_fps if self.target_fps is not None else src_fps
        # 원본에서 몇 프레임마다 1프레임을 추출할지 계산
        frame_step  = max(1, round(src_fps / out_fps))

        writer = None
        if self.save_video:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(vid_out_path), fourcc, out_fps, (width, height))

        norm_result = {
            "model": "mediapipe",
            "variant": MODEL_NAME.replace(".task", ""),
            "video_file": self.video_path.name,
            "metadata": self.metadata,
            "normalization": {
                "steps": ["hip_center", "torso_scale", "direction_canonical"],
                "canonical_direction": "head_right",
                "coordinate_note": "hip_centered, torso_scaled (unitless, original unit: normalized 0~1)",
                "confidence_thresholds": {"high": VIS_HIGH, "low": VIS_LOW},
            },
            "source_fps": src_fps,
            "output_fps": out_fps,
            "frame_step": frame_step,
            "width": width,
            "height": height,
            "keypoint_format": "coco_17",
            "frames": [],
        }

        t_infer_total = 0.0
        t_norm_total  = 0.0
        src_frame_id  = 0   # 원본 영상의 프레임 번호
        out_frame_id  = 0   # 실제 처리된 프레임 번호

        options = _build_options(self._model_path, self._use_gpu)
        print(f"  {'GPU delegate' if self._use_gpu else 'CPU'} 로 처리 중: {self.video_path.name}")
        print(f"  원본 {src_fps:.1f}fps → 처리 {out_fps:.1f}fps (step={frame_step})")

        with PoseLandmarker.create_from_options(options) as landmarker:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 지정된 step에 해당하는 프레임만 처리
                if src_frame_id % frame_step != 0:
                    src_frame_id += 1
                    continue

                timestamp_ms = int(src_frame_id * 1000 / src_fps)

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                )

                t0 = time.perf_counter()
                res = landmarker.detect_for_video(mp_image, timestamp_ms)
                t_infer_total += time.perf_counter() - t0

                norm_frame = {"frame_id": out_frame_id, "src_frame_id": src_frame_id,
                              "timestamp_ms": timestamp_ms,
                              "pose_detected": False, "persons": []}

                t1 = time.perf_counter()
                for person_lms in res.pose_landmarks:
                    coco_pts = _extract_coco_keypoints(person_lms)

                    norm_frame["persons"].append(_normalize_person(coco_pts))
                    if self.save_video:
                        _draw_coco_skeleton(frame, coco_pts)

                norm_frame["pose_detected"] = len(res.pose_landmarks) > 0
                t_norm_total += time.perf_counter() - t1

                norm_result["frames"].append(norm_frame)

                if writer is not None:
                    writer.write(frame)

                src_frame_id += 1
                out_frame_id += 1
                if out_frame_id % 100 == 0:
                    print(f"    처리 {out_frame_id} / 원본 {src_frame_id}/{total} frames …", end="\r")

        cap.release()
        if writer is not None:
            writer.release()

        norm_result["total_frames"] = out_frame_id

        with open(norm_json_path, "w", encoding="utf-8") as f:
            json.dump(norm_result, f, ensure_ascii=False, indent=2)

        if out_frame_id > 0:
            fps_eff = out_frame_id / (t_infer_total + t_norm_total) if (t_infer_total + t_norm_total) > 0 else 0
            print(
                f"\n  {self.video_path.name}  처리 프레임={out_frame_id} (원본 {src_frame_id}프레임)\n"
                f"    추론 합계: {t_infer_total:.2f}s  ({t_infer_total/out_frame_id*1000:.1f} ms/f)\n"
                f"    정규화 합계: {t_norm_total:.2f}s  ({t_norm_total/out_frame_id*1000:.2f} ms/f)\n"
                f"    총 처리속도: {fps_eff:.1f} fps"
            )

        return {
            "normalized":     norm_result,
            "norm_json_path": norm_json_path,
            "video_path":     vid_out_path,
        }


def vision(
    video_url: str | Path,
    user_id,
    exercise_id,
    start_at,
    *,
    upload_root: str | Path | None = None,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    save_video: bool = False,
    fps: float | None = None,
) -> dict:
    """
    다른 Python 파일에서 workout_point_model = vision 형태로 사용할 수 있는 함수.

    저장 경로:
    C:\\posefit_saves\\{user_id}\\{exercise_id}\\pose_point\\{user_id}_{exercise_id}_{start_at}.json
    """
    video_path = _resolve_video_path(video_url, upload_root=upload_root)
    norm_json_path = _build_pose_point_json_path(
        user_id=user_id,
        exercise_id=exercise_id,
        start_at=start_at,
        output_root=output_root,
    )

    estimator = MediaPipePoseEstimator(
        video_path=video_path,
        output_path=norm_json_path.parent,
        save_video=save_video,
        fps=fps,
        output_json_path=norm_json_path,
        metadata={
            "user_id": user_id,
            "exercise_id": exercise_id,
            "start_at": start_at,
            "video_url": video_url,
        },
    )
    result = estimator.run()
    return {
        "normalized":     result["normalized"],
        "norm_json_path": result["norm_json_path"],
    }


def run_batch(
    test_folder: str | Path,
    output_root: str | Path,
    save_video: bool = False,
    fps: float | None = None,
) -> list[dict]:
    """test_folder 안의 동영상 파일을 모두 순회하며 포즈 추정을 실행한다."""
    test_folder = Path(test_folder)
    output_root = Path(output_root)
    video_exts  = {".mp4", ".mov", ".avi", ".mkv"}
    video_files = [p for p in sorted(test_folder.iterdir()) if p.suffix.lower() in video_exts]

    if not video_files:
        print(f"동영상 파일 없음: {test_folder}")
        return []

    results = []
    for i, video_path in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] {video_path.name}")
        estimator = MediaPipePoseEstimator(
            video_path=video_path,
            output_path=output_root,
            save_video=save_video,
            fps=fps,
        )
        results.append(estimator.run())
    return results
