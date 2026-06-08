"""
fusion_track.py - 얼굴 인식 + ByteTrack 융합 추적

실행:
    python fusion_track.py                  # 최초 인식된 1인 자동 추적
    python fusion_track.py --source video.mp4

동작:
    [SEARCHING]  face_recognition 실행
      - 화면 속 person bbox 를 스캔하여 등록된 얼굴이 인식되면 즉시 TRACKING 전환
      - 인식 실패한 ID 는 face-interval 프레임마다 재시도

    [TRACKING]   face_recognition 완전 종료
      - 확정된 track_id 의 bbox 만 초록색으로 강조, 나머지 person 무시
      - 타겟 bbox 소멸(화면 이탈 / ID 변경) → SEARCHING 재전환

모델 파일 (최초 실행 시 자동 다운로드):
    yolo11n.pt  (~5 MB)

사전 준비:
    data/encodings.bin  — collect_faces.py 로 먼저 얼굴 등록 필요
"""

import argparse
import os
import pickle

import cv2
import face_recognition
import numpy as np

# ── 경로 ────────────────────────────────────────────────────────
DATA_DIR      = os.path.join(os.path.dirname(__file__), "data")
ENCODINGS_BIN = os.path.join(DATA_DIR, "encodings.bin")

# ── 기본 설정 ────────────────────────────────────────────────────
FACE_REGION_RATIO = 0.55   # person bbox 상단 몇 % 를 얼굴 영역으로 사용
FACE_INTERVAL     = 15     # SEARCHING 중 인식 실패한 ID 재시도 주기 (프레임)
TOLERANCE         = 0.5    # 얼굴 인식 임계값 (낮을수록 엄격)

# ── 색상 (BGR) ───────────────────────────────────────────────────
C_TARGET  = (60, 220,  60)   # 타겟 (초록)
C_SEARCH  = (100, 100, 100)  # SEARCHING 중 미인식 person (회색)
C_BLACK   = (0,    0,   0)


class FusionTracker:
    """얼굴 인식(face_recognition) + YOLO11 + ByteTrack 융합 추적기.

    Parameters
    ----------
    model_name    : YOLO 모델 (기본: yolo11n.pt)
    conf          : YOLO 검출 신뢰도 임계값 (기본: 0.4)
    face_interval : SEARCHING 중 인식 실패한 ID 재시도 주기 (기본: 15)
    tolerance     : 얼굴 인식 임계값 (기본: 0.5)
    """

    def __init__(
        self,
        model_name: str    = "yolo11n.pt",
        conf: float        = 0.4,
        face_interval: int = FACE_INTERVAL,
        tolerance: float   = TOLERANCE,
    ):
        from ultralytics import YOLO

        self.yolo          = YOLO(model_name)
        self.conf          = conf
        self.face_interval = face_interval
        self.tolerance     = tolerance

        self._known_encodings, self._known_names = self._load_encodings()

        # 상태: _target_id is None → SEARCHING, 아니면 TRACKING
        self._target_id:   int | None = None
        self._target_name: str | None = None
        self._seen_ids:    set[int]   = set()   # 이미 시도한 ID (즉시 재시도 방지)
        self._frame_idx = 0

    # ── 인코딩 로드 ─────────────────────────────────────────────
    @staticmethod
    def _load_encodings() -> tuple[list, list]:
        if not os.path.exists(ENCODINGS_BIN):
            raise FileNotFoundError(
                f"{ENCODINGS_BIN} 없음 — collect_faces.py 로 먼저 얼굴을 등록하세요."
            )
        with open(ENCODINGS_BIN, "rb") as f:
            data = pickle.load(f)
        encodings, names = data["encodings"], data["names"]
        print(f"[Fusion] 인코딩 로드: {len(encodings)}개  ({len(set(names))}명)")
        return encodings, names

    # ── bbox 상단 크롭 → 이름 인식 ─────────────────────────────
    def _recognize_person(
        self, frame: np.ndarray, x1: int, y1: int, x2: int, y2: int
    ) -> str | None:
        face_y2 = y1 + int((y2 - y1) * FACE_REGION_RATIO)
        crop    = frame[y1:face_y2, x1:x2]
        if crop.size == 0:
            return None

        rgb       = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model="hog")
        if not locations:
            return None

        encodings = face_recognition.face_encodings(rgb, locations)
        for enc in encodings:
            distances = face_recognition.face_distance(self._known_encodings, enc)
            if len(distances) == 0:
                continue
            best = int(np.argmin(distances))
            if distances[best] <= self.tolerance:
                return self._known_names[best]
        return None

    # ── 메인 추적 루프 ──────────────────────────────────────────
    def run(self, source: int | str = 0) -> None:
        """추적 루프 실행. q / ESC 로 종료."""
        print(f"[Fusion] source={source}  q/ESC=종료")
        print("[Fusion] SEARCHING — 등록된 얼굴이 인식되면 추적을 시작합니다.\n")

        for result in self.yolo.track(
            source=source,
            conf=self.conf,
            tracker="bytetrack.yaml",
            classes=[0],    # person 클래스만
            stream=True,
            verbose=False,
        ):
            frame      = result.orig_img.copy()
            active_ids: set[int] = set()
            retry_tick = (self._frame_idx % self.face_interval == 0)

            if result.boxes is not None:
                for box in result.boxes:
                    if box.id is None:
                        continue

                    track_id        = int(box.id.item())
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    active_ids.add(track_id)

                    # ── TRACKING: 타겟 외 모든 person 무시 ──────────
                    if self._target_id is not None:
                        if track_id == self._target_id:
                            label = f"ID:{track_id}  {self._target_name}"
                            self._draw_box(frame, x1, y1, x2, y2, label, C_TARGET)
                        # 타겟이 아닌 person: 아무것도 그리지 않음
                        continue

                    # ── SEARCHING: face_recognition 실행 ────────────
                    is_new = track_id not in self._seen_ids
                    if is_new or retry_tick:
                        self._seen_ids.add(track_id)
                        name = self._recognize_person(frame, x1, y1, x2, y2)
                        if name:
                            self._target_id   = track_id
                            self._target_name = name
                            print(f"[Fusion] LOCKED → ID:{track_id}  '{name}'  (face recog 종료)")
                            # 이번 프레임에서 바로 타겟 박스 그리기
                            label = f"ID:{track_id}  {name}"
                            self._draw_box(frame, x1, y1, x2, y2, label, C_TARGET)
                            continue

                    # 아직 인식 안 된 person: 회색 박스
                    cv2.rectangle(frame, (x1, y1), (x2, y2), C_SEARCH, 1)

            # ── 타겟 소멸 확인 → SEARCHING 재전환 ───────────────
            if self._target_id is not None and self._target_id not in active_ids:
                print(f"[Fusion] LOST → ID:{self._target_id} ('{self._target_name}')  SEARCHING 재시작")
                self._target_id   = None
                self._target_name = None
                self._seen_ids.clear()

            self._frame_idx += 1
            self._draw_state_hud(frame)
            cv2.imshow("Fusion Tracker", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

        cv2.destroyAllWindows()

    # ── UI 헬퍼 ─────────────────────────────────────────────────
    def _draw_state_hud(self, frame: np.ndarray) -> None:
        if self._target_id is None:
            msg   = "SEARCHING..."
            color = C_SEARCH
        else:
            msg   = f"TRACKING  '{self._target_name}'"
            color = C_TARGET
        cv2.putText(frame, msg, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, C_BLACK, 3, cv2.LINE_AA)
        cv2.putText(frame, msg, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color,   2, cv2.LINE_AA)

    @staticmethod
    def _draw_box(
        frame: np.ndarray,
        x1: int, y1: int, x2: int, y2: int,
        label: str,
        color: tuple[int, int, int],
    ) -> None:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0]
        cv2.rectangle(frame, (x1, y1 - lh - 8), (x1 + lw + 6, y1), color, -1)
        cv2.putText(frame, label, (x1 + 3, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_BLACK, 1, cv2.LINE_AA)


# ── CLI ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="얼굴 인식 + ByteTrack 융합 추적")
    parser.add_argument("--source", default="0",
                        help="입력 소스 (0=웹캠, 파일 경로)  [기본: 0]")
    parser.add_argument("--conf", type=float, default=0.4,
                        help="검출 신뢰도 임계값  [기본: 0.4]")
    parser.add_argument("--model", default="yolo11n.pt",
                        help="YOLO 모델  [기본: yolo11n.pt]")
    parser.add_argument("--face-interval", type=int, default=FACE_INTERVAL,
                        help=f"SEARCHING 중 재시도 주기 (프레임 수)  [기본: {FACE_INTERVAL}]")
    parser.add_argument("--tolerance", type=float, default=TOLERANCE,
                        help=f"얼굴 인식 임계값  [기본: {TOLERANCE}]")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source

    FusionTracker(
        model_name    = args.model,
        conf          = args.conf,
        face_interval = args.face_interval,
        tolerance     = args.tolerance,
    ).run(source)


if __name__ == "__main__":
    main()
