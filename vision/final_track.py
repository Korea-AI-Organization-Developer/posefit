"""
final_track.py - YOLO11 + ByteTrack 다중 객체 추적

실행:
    python final_track.py
    python final_track.py --source video.mp4
    python final_track.py --conf 0.4

모델 파일 (최초 실행 시 자동 다운로드):
    yolo11n.pt  (~5 MB)
"""

import argparse
import cv2


class ByteTrackTracker:
    """YOLO11 + ByteTrack 다중 객체 추적기.

    Parameters
    ----------
    model_name : str
        ultralytics YOLO 모델 이름 (기본: yolo11n.pt)
    conf : float
        검출 신뢰도 임계값 (기본: 0.3)
    """

    def __init__(self, model_name: str = "yolo11n.pt", conf: float = 0.3):
        from ultralytics import YOLO
        self.model = YOLO(model_name)
        self.conf  = conf

    def run(self, source: int | str = 0) -> None:
        """추적 루프 실행. q / ESC 로 종료.

        Parameters
        ----------
        source : int | str
            0 = 웹캠, 또는 영상 파일 경로
        """
        print(f"[ByteTrack] source={source}  conf={self.conf}  q/ESC=종료")

        for result in self.model.track(
            source=source,
            conf=self.conf,
            tracker="bytetrack.yaml",
            stream=True,
            verbose=False,
        ):
            frame = result.plot()
            cv2.imshow("ByteTrack", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

        cv2.destroyAllWindows()


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
