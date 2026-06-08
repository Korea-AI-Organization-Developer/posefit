"""
tracking.py - 객체 추적 테스트 파이프라인

실행:
    python tracking.py --method bytetrack           # YOLO11 + ByteTrack (다중 객체)
    python tracking.py --method sam                 # SAM2 클릭 선택 추적 (단일 객체)
    python tracking.py --method bytetrack --source video.mp4
    python tracking.py --method bytetrack --conf 0.4

클래스:
    ByteTrackTracker  YOLO11 + ByteTrack 기반 다중 객체 추적
    SAMTracker        SAM2 기반 클릭-선택 단일 객체 세그멘테이션 추적

모델 파일 (최초 실행 시 자동 다운로드):
    yolo11n.pt      — YOLO11 nano  (~5 MB)
    sam2.1_b.pt     — SAM2 base   (~76 MB)
"""

import argparse
import cv2
import numpy as np


# ─────────────────────────────────────────────
# ByteTrack Tracker
# ─────────────────────────────────────────────

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
        """추적 루프 실행.

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


# ─────────────────────────────────────────────
# SAM Tracker
# ─────────────────────────────────────────────

class SAMTracker:
    """SAM2 기반 클릭-선택 단일 객체 추적기.

    클릭한 지점을 프롬프트로 SAM2가 해당 프레임을 세그멘테이션하고,
    다음 프레임부터는 이전 마스크의 무게중심을 새 프롬프트로 사용하여 추적합니다.

    Parameters
    ----------
    model_name : str
        ultralytics SAM2 모델 이름 (기본: sam2.1_b.pt)
    """

    def __init__(self, model_name: str = "sam2.1_b.pt"):
        from ultralytics import SAM
        self.model     = SAM(model_name)
        self._point    = None   # (x, y) 클릭 좌표
        self._tracking = False

    # ── 마우스 콜백 ──────────────────────────────
    def _mouse_cb(self, event, x: int, y: int, _flags, _param) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self._point    = (x, y)
            self._tracking = True
            print(f"[SAM] 선택: ({x}, {y})  — 추적 시작")

    # ── 실행 루프 ────────────────────────────────
    def run(self, source: int | str = 0) -> None:
        """추적 루프 실행.

        Parameters
        ----------
        source : int | str
            0 = 웹캠, 또는 영상 파일 경로
        """
        src = int(source) if str(source).isdigit() else source
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print("[Error] 카메라/영상을 열 수 없습니다.")
            return

        cv2.namedWindow("SAM Tracker")
        cv2.setMouseCallback("SAM Tracker", self._mouse_cb)

        prev_mask: np.ndarray | None = None
        print("[SAM] 추적할 객체를 클릭하세요.  q/ESC=종료")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            display = frame.copy()

            if self._tracking and self._point is not None:
                # 이전 마스크가 있으면 그 무게중심을, 없으면 클릭 좌표를 프롬프트로 사용
                if prev_mask is not None:
                    prompt_pt = list(self._centroid(prev_mask))
                else:
                    prompt_pt = list(self._point)

                results = self.model.predict(
                    frame,
                    points=[prompt_pt],
                    labels=[1],
                    verbose=False,
                )

                if results and results[0].masks is not None:
                    # 마스크를 프레임 크기로 리사이즈
                    raw  = results[0].masks.data[0].cpu().numpy().astype(np.uint8)
                    mask = cv2.resize(
                        raw,
                        (frame.shape[1], frame.shape[0]),
                        interpolation=cv2.INTER_NEAREST,
                    )
                    prev_mask = mask
                    display   = self._overlay(display, mask)

                    cx, cy = self._centroid(mask)
                    cv2.circle(display, (cx, cy), 6, (0, 255, 0), -1)
                else:
                    # 추적 실패 시 초기화 (다시 클릭하도록)
                    prev_mask = None

            self._draw_hud(display, self._tracking)
            cv2.imshow("SAM Tracker", display)

            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

        cap.release()
        cv2.destroyAllWindows()

    # ── 헬퍼 ─────────────────────────────────────
    @staticmethod
    def _centroid(mask: np.ndarray) -> tuple[int, int]:
        m = cv2.moments(mask)
        if m["m00"] == 0:
            h, w = mask.shape
            return w // 2, h // 2
        return int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])

    @staticmethod
    def _overlay(
        frame: np.ndarray,
        mask: np.ndarray,
        color: tuple[int, int, int] = (0, 120, 255),
        alpha: float = 0.45,
    ) -> np.ndarray:
        overlay          = frame.copy()
        overlay[mask == 1] = color
        return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    @staticmethod
    def _draw_hud(frame: np.ndarray, tracking: bool) -> None:
        status = "Tracking..." if tracking else "Click to select object"
        color  = (0, 255, 255) if tracking else (200, 200, 200)
        cv2.putText(frame, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
        if tracking:
            cv2.putText(frame, "Click again to reselect", (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 180, 180), 1, cv2.LINE_AA)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="객체 추적 테스트 파이프라인",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--method",
        choices=["bytetrack", "sam"],
        default="bytetrack",
        help="추적 방법\n  bytetrack : YOLO11 + ByteTrack (다중 객체)\n  sam       : SAM2 클릭 선택 (단일 객체)",
    )
    parser.add_argument(
        "--source",
        default="0",
        help="입력 소스 (0=웹캠, 파일 경로 등)  [기본: 0]",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.3,
        help="ByteTrack 검출 신뢰도 임계값  [기본: 0.3]",
    )
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source

    if args.method == "bytetrack":
        ByteTrackTracker(conf=args.conf).run(source)
    else:
        SAMTracker().run(source)


if __name__ == "__main__":
    main()
