"""얼굴 임베딩 추출 및 비교."""

import base64
import pickle

import numpy as np
from deepface import DeepFace

MODEL = "Facenet512"
THRESHOLD = 0.40  # 코사인 거리 임계값 (낮을수록 엄격)


def _decode_image(base64_str: str) -> str:
    """base64 이미지를 임시 파일로 저장 후 경로 반환."""
    import tempfile, os
    header, data = base64_str.split(",", 1) if "," in base64_str else ("", base64_str)
    img_bytes = base64.b64decode(data)
    suffix = ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(img_bytes)
    tmp.close()
    return tmp.name


def extract_embedding(base64_image: str) -> bytes:
    """이미지에서 얼굴 임베딩 벡터를 추출해 직렬화된 bytes로 반환."""
    img_path = _decode_image(base64_image)
    try:
        result = DeepFace.represent(
            img_path=img_path,
            model_name=MODEL,
            enforce_detection=True,
            detector_backend="opencv",
        )
        vector = np.array(result[0]["embedding"], dtype=np.float32)
        return pickle.dumps(vector)
    finally:
        import os
        os.unlink(img_path)


def compare_embedding(stored_bytes: bytes, base64_image: str) -> float:
    """저장된 임베딩과 새 이미지를 비교해 코사인 거리(0~1) 반환. 낮을수록 같은 사람."""
    img_path = _decode_image(base64_image)
    try:
        stored_vec: np.ndarray = pickle.loads(stored_bytes)
        result = DeepFace.represent(
            img_path=img_path,
            model_name=MODEL,
            enforce_detection=True,
            detector_backend="opencv",
        )
        new_vec = np.array(result[0]["embedding"], dtype=np.float32)

        # 코사인 거리
        dot = np.dot(stored_vec, new_vec)
        norm = np.linalg.norm(stored_vec) * np.linalg.norm(new_vec)
        cosine_similarity = dot / (norm + 1e-10)
        return float(1 - cosine_similarity)
    finally:
        import os
        os.unlink(img_path)


def is_same_person(stored_bytes: bytes, base64_image: str) -> tuple[bool, float]:
    """같은 사람인지 판단. (매칭 여부, 거리값) 반환."""
    distance = compare_embedding(stored_bytes, base64_image)
    return distance < THRESHOLD, distance
