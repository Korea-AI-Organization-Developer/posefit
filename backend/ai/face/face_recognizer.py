import io

import face_recognition
import numpy as np
from PIL import Image

MODEL_VERSION = "dlib-v1"


def extract_encoding(image_bytes: bytes) -> np.ndarray:
    """이미지 바이트 → 128차원 얼굴 임베딩.

    Raises
    ------
    ValueError("FACE_NOT_DETECTED")      얼굴 없음
    ValueError("MULTIPLE_FACES_DETECTED") 두 명 이상
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(img)

    locations = face_recognition.face_locations(arr)
    if len(locations) == 0:
        raise ValueError("FACE_NOT_DETECTED")
    if len(locations) > 1:
        raise ValueError("MULTIPLE_FACES_DETECTED")

    encodings = face_recognition.face_encodings(arr, locations)
    return encodings[0]  # 128-dim float64


def encoding_to_bytes(encoding: np.ndarray) -> bytes:
    """numpy 배열 → DB 저장용 bytes (128 * 8 = 1024 bytes)."""
    return encoding.astype(np.float64).tobytes()


def bytes_to_encoding(data: bytes) -> np.ndarray:
    """DB bytes → numpy 배열."""
    return np.frombuffer(data, dtype=np.float64)


def count_faces(image_bytes: bytes) -> int:
    """얼굴 수만 반환 — 임베딩 추출 없이 위치만 검출해 빠르다."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return len(face_recognition.face_locations(np.array(img)))


def is_match(stored: bytes, candidate: bytes, tolerance: float = 0.5) -> bool:
    """등록 임베딩과 후보 임베딩 비교. tolerance 이하면 동일인."""
    enc_stored = bytes_to_encoding(stored)
    enc_candidate = bytes_to_encoding(candidate)
    distance = face_recognition.face_distance([enc_stored], enc_candidate)[0]
    return float(distance) <= tolerance
