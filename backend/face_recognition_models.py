"""face_recognition_models pkg_resources 호환 shim.

face_recognition_models 0.3.0은 pkg_resources를 사용하는데,
uv 환경에서 pkg_resources가 없는 경우 ImportError가 발생한다.
이 파일이 backend/ (sys.path 최상위)에 있으면 설치된 패키지보다 먼저 로드되어
pkg_resources 없이 모델 경로를 반환한다.
"""
import os
import sys


def _models_dir() -> str:
    for p in sys.path:
        candidate = os.path.join(p, "face_recognition_models", "models")
        if os.path.isdir(candidate):
            return candidate
    raise RuntimeError("face_recognition_models 패키지를 찾을 수 없습니다. uv sync를 실행하세요.")


def pose_predictor_model_location() -> str:
    return os.path.join(_models_dir(), "shape_predictor_68_face_landmarks.dat")


def pose_predictor_five_point_model_location() -> str:
    return os.path.join(_models_dir(), "shape_predictor_5_face_landmarks.dat")


def face_recognition_model_location() -> str:
    return os.path.join(_models_dir(), "dlib_face_recognition_resnet_model_v1.dat")


def cnn_face_detector_model_location() -> str:
    return os.path.join(_models_dir(), "mmod_human_face_detector.dat")
