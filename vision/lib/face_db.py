import os
import pickle

_VISION_DIR   = os.path.dirname(os.path.dirname(__file__))
DEFAULT_PATH  = os.path.join(_VISION_DIR, "data", "encodings.bin")


class FaceDB:
    """얼굴 인코딩 DB 로드 유틸리티."""

    @staticmethod
    def load(path: str = DEFAULT_PATH) -> tuple[list, list]:
        """encodings.bin 로드 → (encodings, names) 반환."""
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{path} 없음 — collect_faces.py 로 먼저 얼굴을 등록하세요."
            )
        with open(path, "rb") as f:
            data = pickle.load(f)
        return data["encodings"], data["names"]
