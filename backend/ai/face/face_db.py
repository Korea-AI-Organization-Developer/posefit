import os
import pickle


class FaceDB:
    """얼굴 인코딩 DB 로드 유틸리티."""

    @staticmethod
    def load(path: str | None = None) -> tuple[list, list]:
        """encodings.bin 로드 → (encodings, names) 반환.

        Parameters
        ----------
        path : str | None
            encodings.bin 경로. None 이면 ./data/encodings.bin 사용.
        """
        if path is None:
            path = os.path.join(os.getcwd(), "data", "encodings.bin")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{path} 없음 — collect_faces.py 로 먼저 얼굴을 등록하세요."
            )
        with open(path, "rb") as f:
            data = pickle.load(f)
        return data["encodings"], data["names"]
