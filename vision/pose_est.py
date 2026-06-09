"""
pose_est.py - Pose Estimation 테스트 파이프라인

실행:
    python pose_est.py --model mediapipe
    python pose_est.py --model vitpose
    python pose_est.py --model detrpose
    python pose_est.py --model mediapipe --source video.mp4

종료 시 {model}_{YYYYMMDD_HHMMSS}.json 자동 저장
"""

import argparse
from lib.pose_estimator import (
    PoseEstimatorBase,
    MediaPipePoseEstimator,
    ViTPoseEstimator,
    DETRPoseEstimator,
)

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
    parser.add_argument(
        "--angle-conf", type=float, default=0.0, metavar="THR",
        help="관절 각도 계산 시 신뢰도 임계값  [기본: 0.0]",
    )
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    _MODELS[args.model]().run(source, angle_conf_thr=args.angle_conf)


if __name__ == "__main__":
    main()
