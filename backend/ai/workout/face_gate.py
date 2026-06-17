"""
운동 진입 얼굴 게이트

FastAPI WebSocket / 로컬 카메라 양쪽에서 사용 가능한 클래스형 얼굴 인증 라이브러리.

흐름:
    1. DB 미등록  → 얼굴 캡쳐·학습 → DB 저장 → 얼굴 인증 단계로 자동 전환
    2. DB 등록    → 얼굴 인증
       - 통과 (연속 N 프레임 성공) → PASSED
       - 연속 M 프레임 실패        → REGISTRATION 으로 되돌아감 (재캡쳐)

참조: backend/ai/workout/ref/face_registration.py
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

import cv2
import face_recognition
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import FaceEmbedding

MODEL_VERSION = "face_recognition-v1"

# ── 기본 설정 상수 ──────────────────────────────────────────────
_SAMPLES_NEEDED        = 40
_CAPTURE_INTERVAL      = 0.2       # 초
_RECOGNITION_THRESHOLD = 0.45      # 거리 임계값 (낮을수록 엄격)
_VERIFY_STREAK_NEEDED  = 3         # 통과 판정 연속 성공 프레임 수
_VERIFY_FAIL_LIMIT     = 10        # 재등록 트리거 연속 실패 프레임 수
_CAM_W, _CAM_H         = 640, 480
_GUIDE_W_RATIO         = 0.52
_GUIDE_H_RATIO         = 0.72
_MIN_FACE_RATIO        = 0.10
_FACE_PADDING          = 0.30

# ── BGR 색상 ────────────────────────────────────────────────────
_GREEN  = ( 60, 220,  60)
_RED    = ( 60,  60, 220)
_YELLOW = (  0, 200, 220)
_WHITE  = (255, 255, 255)
_BLACK  = (  0,   0,   0)
_DARK   = ( 30,  30,  30)
_GRAY   = (140, 140, 140)


class GateMode(str, Enum):
    REGISTRATION = "registration"
    VERIFICATION = "verification"
    PASSED       = "passed"
    FAILED       = "failed"


@dataclass
class FrameResult:
    """process_frame 의 반환 타입."""

    mode:    GateMode
    message: str
    progress: int = 0             # 등록: 수집 샘플 수 / 인증: 연속 성공 수
    total:    int = 0             # 목표치 (samples_needed 또는 verify_streak_needed)
    face_in_guide: bool = False   # 얼굴이 가이드 박스 안에 정상 위치한 경우 True
    annotated_frame: bytes | None = None   # JPEG bytes (encode_result=True 시)


# ── 인코딩 ↔ bytes ───────────────────────────────────────────────

def encoding_to_bytes(enc: np.ndarray) -> bytes:
    """128-d float64 인코딩을 1024 bytes 로 직렬화한다."""
    return enc.astype(np.float64).tobytes()


def bytes_to_encoding(data: bytes) -> np.ndarray:
    """DB 에서 읽은 bytes 를 128-d float64 배열로 역직렬화한다."""
    return np.frombuffer(data, dtype=np.float64)


class WorkoutFaceGate:
    """
    운동 진입 시 얼굴 등록·인증 상태머신.

    Parameters
    ----------
    user_id
        인증 대상 사용자의 DB ID.
    samples_needed
        등록 완료까지 수집할 얼굴 샘플 수.
    capture_interval
        샘플 캡쳐 최소 간격(초). 너무 연속된 캡쳐를 막는다.
    recognition_threshold
        face_recognition 거리 임계값 (0 ~ 1). 낮을수록 엄격한 인증.
    verify_streak_needed
        인증 통과 판정에 필요한 연속 성공 프레임 수.
    verify_fail_limit
        재등록으로 전환하는 연속 실패 프레임 수.
    cam_w, cam_h
        로컬 run_local() 카메라 해상도.
    guide_w_ratio, guide_h_ratio
        화면 대비 가이드 박스 크기 비율.
    min_face_ratio
        가이드 박스 대비 최소 얼굴 크기 비율.
    face_padding
        캡쳐 시 얼굴 크롭 여백 비율.
    """

    def __init__(
        self,
        user_id: int,
        *,
        samples_needed: int          = _SAMPLES_NEEDED,
        capture_interval: float      = _CAPTURE_INTERVAL,
        recognition_threshold: float = _RECOGNITION_THRESHOLD,
        verify_streak_needed: int    = _VERIFY_STREAK_NEEDED,
        verify_fail_limit: int       = _VERIFY_FAIL_LIMIT,
        cam_w: int                   = _CAM_W,
        cam_h: int                   = _CAM_H,
        guide_w_ratio: float         = _GUIDE_W_RATIO,
        guide_h_ratio: float         = _GUIDE_H_RATIO,
        min_face_ratio: float        = _MIN_FACE_RATIO,
        face_padding: float          = _FACE_PADDING,
    ) -> None:
        self.user_id               = user_id
        self.samples_needed        = samples_needed
        self.capture_interval      = capture_interval
        self.recognition_threshold = recognition_threshold
        self.verify_streak_needed  = verify_streak_needed
        self.verify_fail_limit     = verify_fail_limit
        self.cam_w                 = cam_w
        self.cam_h                 = cam_h
        self.guide_w_ratio         = guide_w_ratio
        self.guide_h_ratio         = guide_h_ratio
        self.min_face_ratio        = min_face_ratio
        self.face_padding          = face_padding

        # 런타임 상태
        self._mode: GateMode                = GateMode.REGISTRATION
        self._collected: list[np.ndarray]   = []   # RGB 얼굴 이미지 목록 (등록용)
        self._stored_enc: np.ndarray | None = None
        self._verify_streak: int            = 0
        self._verify_fails: int             = 0
        self._last_cap_time: float          = 0.0
        self._ready_to_encode: bool         = False

        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    # ═══════════════════════════════════════════════════════════════
    # Public async API  ─── FastAPI / WebSocket 핸들러에서 호출
    # ═══════════════════════════════════════════════════════════════

    @property
    def mode(self) -> GateMode:
        return self._mode

    async def initialize(
        self, db: AsyncSession, *, force_registration: bool = False
    ) -> GateMode:
        """
        DB 를 조회해 초기 모드를 결정하고 반환한다.

        - 얼굴 미등록 → GateMode.REGISTRATION
        - 얼굴 등록됨 → GateMode.VERIFICATION (임베딩 로드)
        - force_registration=True 이면 DB 에 임베딩이 있어도 REGISTRATION 으로 강제
        """
        row = await self._db_get_face(db)
        if row is not None:
            self._stored_enc = bytes_to_encoding(row.embedding)
            self._mode = GateMode.REGISTRATION if force_registration else GateMode.VERIFICATION
        else:
            self._mode = GateMode.REGISTRATION
        return self._mode

    async def process_frame(
        self,
        frame_bytes: bytes,
        db: AsyncSession,
        *,
        encode_result: bool = False,
    ) -> FrameResult:
        """
        JPEG/PNG 프레임 바이트를 받아 현재 모드에 따라 처리 후 FrameResult 를 반환한다.
        WebSocket 루프에서 매 프레임마다 호출한다.

        Parameters
        ----------
        frame_bytes
            클라이언트에서 전송한 JPEG 또는 PNG 바이트.
        db
            비동기 DB 세션.
        encode_result
            True 이면 어노테이션 프레임을 JPEG bytes 로 FrameResult.annotated_frame 에 포함.
        """
        frame = _decode_frame(frame_bytes)
        if frame is None:
            return FrameResult(self._mode, "프레임 디코딩 실패")

        frame = cv2.flip(frame, 1)

        if self._mode == GateMode.REGISTRATION:
            return await self._do_registration(frame, db, encode_result)
        if self._mode == GateMode.VERIFICATION:
            return self._do_verification(frame, encode_result)
        return FrameResult(self._mode, self._mode.value)

    def reset_to_registration(self) -> None:
        """인증 실패 후 수동으로 등록 모드로 초기화한다."""
        self._collected.clear()
        self._verify_streak = 0
        self._verify_fails  = 0
        self._mode          = GateMode.REGISTRATION

    # ═══════════════════════════════════════════════════════════════
    # 로컬 카메라 루프  ─── 개발·테스트 전용
    # ═══════════════════════════════════════════════════════════════

    async def run_local(self, db: AsyncSession, camera_index: int = 0) -> GateMode:
        """
        로컬 카메라를 열어 전체 흐름을 실행한다 (cv2.imshow 사용).
        FastAPI 서버 밖에서 개발·테스트 목적으로 호출한다.

        Returns
        -------
        GateMode.PASSED  — 인증 통과, 운동 진입 가능
        GateMode.FAILED  — q / ESC 로 사용자 종료
        """
        await self.initialize(db)

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError("카메라를 열 수 없습니다")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.cam_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_h)

        window = "PoseFit — Face Gate"
        try:
            while self._mode not in (GateMode.PASSED, GateMode.FAILED):
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)

                if self._mode == GateMode.REGISTRATION:
                    await self._do_registration(frame, db, encode_result=False)
                else:
                    self._do_verification(frame, encode_result=False)

                cv2.imshow(window, frame)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    self._mode = GateMode.FAILED
        finally:
            cap.release()
            cv2.destroyWindow(window)

        return self._mode

    # ═══════════════════════════════════════════════════════════════
    # 내부 — 등록 단계
    # ═══════════════════════════════════════════════════════════════

    async def _do_registration(
        self, frame: np.ndarray, db: AsyncSession, encode_result: bool
    ) -> FrameResult:
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gx1, gy1, gx2, gy2 = self._guide_box(w, h)

        faces = self._detect(gray)
        valid = [f for f in faces if self._in_guide(f, gx1, gy1, gx2, gy2)]

        now = time.time()
        if len(valid) == 1 and now - self._last_cap_time >= self.capture_interval:
            self._collected.append(self._crop_rgb(frame, valid[0]))
            self._last_cap_time = now

        count = len(self._collected)

        if len(faces) == 0:
            color, msg = _YELLOW, "얼굴을 화면에 맞춰주세요"
        elif not valid:
            color, msg = _RED,    "얼굴을 박스 안으로 이동해 주세요"
        elif len(valid) > 1:
            color, msg = _YELLOW, "한 명만 촬영해 주세요"
        else:
            color, msg = _GREEN,  f"촬영 중 {count}/{self.samples_needed}"

        self._draw_ui(
            frame, faces, valid, gx1, gy1, gx2, gy2,
            guide_color=color, status_msg=msg,
            progress=count, total=self.samples_needed,
            header=f"얼굴 등록  |  {count}/{self.samples_needed}  |  q=취소",
        )

        # 샘플 충분 → 1프레임 "등록 중" 표시 후 다음 프레임에서 인코딩
        if count >= self.samples_needed:
            if not self._ready_to_encode:
                self._ready_to_encode = True
                color, msg = _GREEN, "등록 중"
            else:
                enc = self._encode_samples()
                self._ready_to_encode = False
                if enc is not None:
                    await self._db_save_face(db, enc)
                    self._stored_enc = enc
                    self._collected.clear()
                    self._verify_streak = 0
                    self._verify_fails  = 0
                    self._mode          = GateMode.VERIFICATION
                    msg = "등록 완료"
                else:
                    self._collected.clear()
                    msg = "인코딩 실패. 다시 촬영합니다"

        return FrameResult(
            mode=self._mode,
            message=msg,
            progress=count,
            total=self.samples_needed,
            face_in_guide=len(valid) == 1,
            annotated_frame=_jpg(frame) if encode_result else None,
        )

    # ═══════════════════════════════════════════════════════════════
    # 내부 — 인증 단계
    # ═══════════════════════════════════════════════════════════════

    def _do_verification(self, frame: np.ndarray, encode_result: bool) -> FrameResult:
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gx1, gy1, gx2, gy2 = self._guide_box(w, h)

        faces = self._detect(gray)
        valid = [f for f in faces if self._in_guide(f, gx1, gy1, gx2, gy2)]

        verified = False
        if len(valid) == 1 and self._stored_enc is not None:
            rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            fx, fy, fw, fh = valid[0]
            locs = [(fy, fx + fw, fy + fh, fx)]   # (top, right, bottom, left)
            encs = face_recognition.face_encodings(rgb, locs)
            if encs:
                dist     = face_recognition.face_distance([self._stored_enc], encs[0])[0]
                verified = bool(dist <= self.recognition_threshold)

        if verified:
            self._verify_streak += 1
            self._verify_fails   = 0
        else:
            self._verify_streak  = 0
            if valid:   # 박스 안 얼굴이 있는데 실패한 경우만 카운트
                self._verify_fails += 1

        # 상태 전이
        if self._verify_streak >= self.verify_streak_needed:
            self._mode = GateMode.PASSED
            color, msg = _GREEN, "인증 완료! 운동을 시작합니다"
        elif self._verify_fails >= self.verify_fail_limit:
            # 연속 실패 → 재등록
            self._collected.clear()
            self._verify_streak = 0
            self._verify_fails  = 0
            self._mode          = GateMode.REGISTRATION
            color, msg = _RED, "인증 실패. 얼굴을 다시 등록합니다"
        elif len(faces) == 0:
            color, msg = _YELLOW, "얼굴을 화면에 맞춰주세요"
        elif not valid:
            color, msg = _RED,    "얼굴을 박스 안으로 이동해 주세요"
        elif verified:
            color, msg = _GREEN,  f"인증 중 {self._verify_streak}/{self.verify_streak_needed}"
        else:
            color, msg = _RED,    "인식 실패. 정면을 봐 주세요"

        self._draw_ui(
            frame, faces, valid, gx1, gy1, gx2, gy2,
            guide_color=color, status_msg=msg,
            progress=self._verify_streak, total=self.verify_streak_needed,
            header="얼굴 인증  |  q=종료",
        )

        return FrameResult(
            mode=self._mode,
            message=msg,
            progress=self._verify_streak,
            total=self.verify_streak_needed,
            face_in_guide=len(valid) == 1,
            annotated_frame=_jpg(frame) if encode_result else None,
        )

    # ═══════════════════════════════════════════════════════════════
    # 내부 — 비전 헬퍼
    # ═══════════════════════════════════════════════════════════════

    def _detect(self, gray: np.ndarray):
        return self._cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

    def _guide_box(self, w: int, h: int) -> tuple[int, int, int, int]:
        gw  = int(w * self.guide_w_ratio)
        gh  = int(h * self.guide_h_ratio)
        gx1 = (w - gw) // 2
        gy1 = (h - gh) // 2
        return gx1, gy1, gx1 + gw, gy1 + gh

    def _in_guide(self, bbox, gx1: int, gy1: int, gx2: int, gy2: int) -> bool:
        fx, fy, fw, fh = bbox
        cx, cy  = fx + fw // 2, fy + fh // 2
        in_box  = gx1 < cx < gx2 and gy1 < cy < gy2
        size_ok = (
            fw >= (gx2 - gx1) * self.min_face_ratio
            and fh >= (gy2 - gy1) * self.min_face_ratio
        )
        return in_box and size_ok

    def _crop_rgb(self, frame: np.ndarray, bbox) -> np.ndarray:
        h, w           = frame.shape[:2]
        fx, fy, fw, fh = bbox
        px, py         = int(fw * self.face_padding), int(fh * self.face_padding)
        x1, y1         = max(0, fx - px), max(0, fy - py)
        x2, y2         = min(w, fx + fw + px), min(h, fy + fh + py)
        return cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)

    def _encode_samples(self) -> np.ndarray | None:
        """수집된 RGB 샘플들을 face_recognition 으로 인코딩 후 평균 벡터를 반환한다."""
        encs = []
        for rgb in self._collected:
            e = face_recognition.face_encodings(rgb)
            if e:
                encs.append(e[0])
        return np.mean(encs, axis=0) if encs else None

    # ═══════════════════════════════════════════════════════════════
    # 내부 — UI 드로잉
    # ═══════════════════════════════════════════════════════════════

    def _draw_ui(
        self,
        frame: np.ndarray,
        faces,
        valid: list,
        gx1: int, gy1: int, gx2: int, gy2: int,
        *,
        guide_color: tuple,
        status_msg: str,
        progress: int,
        total: int,
        header: str,
    ) -> None:
        h, w = frame.shape[:2]

        # 가이드 박스 반투명 오버레이
        overlay = frame.copy()
        cv2.rectangle(overlay, (gx1, gy1), (gx2, gy2),
                      tuple(c // 6 for c in guide_color), -1)
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

        # 감지된 얼굴 테두리
        for (fx, fy, fw, fh) in faces:
            col = _GREEN if self._in_guide((fx, fy, fw, fh), gx1, gy1, gx2, gy2) else _RED
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), col, 2)

        # 가이드 박스 + 상태 레이블
        _draw_guide_box(frame, gx1, gy1, gx2, gy2, guide_color, status_msg)

        # 가이드 중심 십자선
        cx, cy = (gx1 + gx2) // 2, (gy1 + gy2) // 2
        cv2.line(frame, (cx - 10, cy), (cx + 10, cy), guide_color, 1)
        cv2.line(frame, (cx, cy - 10), (cx, cy + 10), guide_color, 1)

        _draw_top_bar(frame, header, w)
        _draw_progress(frame, progress, total, h, w)

    # ═══════════════════════════════════════════════════════════════
    # 내부 — DB 접근
    # ═══════════════════════════════════════════════════════════════

    async def _db_get_face(self, db: AsyncSession) -> FaceEmbedding | None:
        result = await db.execute(
            select(FaceEmbedding).where(FaceEmbedding.user_id == self.user_id)
        )
        return result.scalar_one_or_none()

    async def _db_save_face(self, db: AsyncSession, enc: np.ndarray) -> None:
        existing = await self._db_get_face(db)
        if existing is not None:
            await db.delete(existing)
            await db.flush()
        face = FaceEmbedding(
            user_id=self.user_id,
            embedding=encoding_to_bytes(enc),
            model_version=MODEL_VERSION,
        )
        db.add(face)
        await db.commit()


# ── 모듈 수준 헬퍼 ─────────────────────────────────────────────────

def _decode_frame(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _jpg(frame: np.ndarray, quality: int = 85) -> bytes:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def _put_text(
    frame: np.ndarray, msg: str, pos: tuple,
    color: tuple = _WHITE, scale: float = 0.6, thick: int = 2,
) -> None:
    cv2.putText(frame, msg, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, _BLACK, thick + 2, cv2.LINE_AA)
    cv2.putText(frame, msg, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color,  thick,     cv2.LINE_AA)


def _draw_guide_box(
    frame: np.ndarray, gx1: int, gy1: int, gx2: int, gy2: int,
    color: tuple, label: str = "",
) -> None:
    r, t = 18, 3
    cv2.ellipse(frame, (gx1 + r, gy1 + r), (r, r), 180, 0, 90, color, t)
    cv2.ellipse(frame, (gx2 - r, gy1 + r), (r, r), 270, 0, 90, color, t)
    cv2.ellipse(frame, (gx2 - r, gy2 - r), (r, r),   0, 0, 90, color, t)
    cv2.ellipse(frame, (gx1 + r, gy2 - r), (r, r),  90, 0, 90, color, t)
    cv2.line(frame, (gx1 + r, gy1), (gx2 - r, gy1), color, t)
    cv2.line(frame, (gx1 + r, gy2), (gx2 - r, gy2), color, t)
    cv2.line(frame, (gx1, gy1 + r), (gx1, gy2 - r), color, t)
    cv2.line(frame, (gx2, gy1 + r), (gx2, gy2 - r), color, t)
    if label:
        lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)[0]
        _put_text(frame, label,
                  ((gx1 + gx2) // 2 - lw // 2, gy2 + lh + 8), color, 0.52, 1)


def _draw_top_bar(frame: np.ndarray, msg: str, w: int) -> None:
    cv2.rectangle(frame, (0, 0), (w, 40), _DARK, -1)
    _put_text(frame, msg, (10, 28), _WHITE, 0.55, 1)


def _draw_progress(frame: np.ndarray, count: int, total: int, h: int, w: int) -> None:
    if total == 0:
        return
    bx1, bx2 = 20, w - 20
    by1, by2 = h - 28, h - 12
    filled   = int((min(count, total) / total) * (bx2 - bx1))
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), _GRAY, -1)
    if filled > 0:
        cv2.rectangle(frame, (bx1, by1), (bx1 + filled, by2), _GREEN, -1)
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), _WHITE, 1)
    pct  = f"{count}/{total}"
    pw, _= cv2.getTextSize(pct, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
    _put_text(frame, pct, (w // 2 - pw // 2, by2 - 2), _WHITE, 0.45, 1)
