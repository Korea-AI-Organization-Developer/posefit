from __future__ import annotations

from dataclasses import dataclass
from typing import Generator

import cv2
import numpy as np


@dataclass
class TrackBox:
    id:   int
    x1:   int
    y1:   int
    x2:   int
    y2:   int
    conf: float


class ByteTrackTracker:
    """YOLO11 + ByteTrack 다중 객체 추적기.

    Parameters
    ----------
    model_name : str
        ultralytics YOLO 모델 이름 (기본: yolo11n.pt)
    conf : float
        검출 신뢰도 임계값 (기본: 0.3)
    classes : list[int] | None
        추적할 클래스 ID 목록. None = 전체, [0] = person only
    """

    def __init__(
        self,
        model_name: str = "yolo11n.pt",
        conf: float = 0.3,
        classes: list[int] | None = None,
    ):
        from ultralytics import YOLO
        self.model   = YOLO(model_name)
        self.conf    = conf
        self.classes = classes

    def stream(
        self, source: int | str = 0
    ) -> Generator[tuple[np.ndarray, list[TrackBox]], None, None]:
        """프레임마다 (원본 프레임, TrackBox 목록) yield."""
        for result in self.model.track(
            source=source,
            conf=self.conf,
            classes=self.classes,
            tracker="bytetrack.yaml",
            stream=True,
            verbose=False,
        ):
            frame = result.orig_img.copy()
            boxes: list[TrackBox] = []
            if result.boxes is not None:
                for box in result.boxes:
                    if box.id is None:
                        continue
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    boxes.append(TrackBox(
                        id=int(box.id.item()),
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        conf=float(box.conf.item()),
                    ))
            yield frame, boxes

    def run(self, source: int | str = 0) -> None:
        """독립 실행 데모. q / ESC 종료."""
        print(f"[ByteTrack] source={source}  conf={self.conf}  q/ESC=종료")
        for result in self.model.track(
            source=source,
            conf=self.conf,
            classes=self.classes,
            tracker="bytetrack.yaml",
            stream=True,
            verbose=False,
        ):
            cv2.imshow("ByteTrack", result.plot())
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
        cv2.destroyAllWindows()
