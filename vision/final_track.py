"""
final_track.py - YOLO11 + ByteTrack 다중 객체 추적

실행:
    python final_track.py
    python final_track.py --source video.mp4
    python final_track.py --conf 0.4
"""

import argparse
from lib.byte_tracker import ByteTrackTracker


def main() -> None:
    parser = argparse.ArgumentParser(description="YOLO11 + ByteTrack 객체 추적")
    parser.add_argument("--source", default="0",
                        help="입력 소스 (0=웹캠, 파일 경로)  [기본: 0]")
    parser.add_argument("--conf", type=float, default=0.3,
                        help="검출 신뢰도 임계값  [기본: 0.3]")
    parser.add_argument("--model", default="yolo11n.pt",
                        help="YOLO 모델  [기본: yolo11n.pt]")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    ByteTrackTracker(model_name=args.model, conf=args.conf).run(source)


if __name__ == "__main__":
    main()
