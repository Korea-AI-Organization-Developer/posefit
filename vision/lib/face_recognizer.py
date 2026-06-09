from __future__ import annotations

import cv2
import numpy as np
import face_recognition
from dataclasses import dataclass

from .face_db import FaceDB, DEFAULT_PATH

UNKNOWN = "Unknown"


@dataclass
class FaceMatch:
    top: int
    right: int
    bottom: int
    left: int
    name: str
    confidence: float  # 0~100


class FaceRecognizer:
    """face_recognition 기반 얼굴 인식기.

    Parameters
    ----------
    encodings_path : str
        encodings.bin 경로 (기본: data/encodings.bin)
    tolerance : float
        인식 임계값 (낮을수록 엄격, 기본: 0.5)
    scale : float
        처리 해상도 축소 비율 (기본: 0.5 → 성능 향상)
    model : str
        "hog" (CPU) 또는 "cnn" (GPU)
    """

    def __init__(
        self,
        encodings_path: str = DEFAULT_PATH,
        tolerance: float = 0.5,
        scale: float = 0.5,
        model: str = "hog",
    ):
        self.tolerance = tolerance
        self.scale     = scale
        self.model     = model
        self._encodings, self._names = FaceDB.load(encodings_path)
        print(f"[FaceRecognizer] {len(self._encodings)}개 인코딩  ({len(set(self._names))}명)")

    def recognize(self, frame: np.ndarray) -> list[FaceMatch]:
        """전체 프레임에서 얼굴 인식. 여러 명 동시 처리."""
        small = cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale)
        rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb, model=self.model)
        encodings = face_recognition.face_encodings(rgb, locations)

        results: list[FaceMatch] = []
        for enc, loc in zip(encodings, locations):
            name, conf = self._match(enc)
            top, right, bottom, left = [int(v / self.scale) for v in loc]
            results.append(FaceMatch(top, right, bottom, left, name, conf))
        return results

    def recognize_crop(self, crop: np.ndarray) -> str | None:
        """크롭된 영역(person bbox 상단 등)에서 인식. 이름 또는 None 반환."""
        if crop.size == 0:
            return None
        rgb       = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model=self.model)
        if not locations:
            return None
        for enc in face_recognition.face_encodings(rgb, locations):
            name, _ = self._match(enc)
            if name != UNKNOWN:
                return name
        return None

    def _match(self, encoding: np.ndarray) -> tuple[str, float]:
        distances = face_recognition.face_distance(self._encodings, encoding)
        if len(distances) == 0 or distances.min() > self.tolerance:
            return UNKNOWN, 0.0
        best = int(np.argmin(distances))
        return self._names[best], (1 - distances[best]) * 100
