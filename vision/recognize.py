"""
얼굴 인식 스크립트

encodings.bin 을 로드하여 웹캠에서 실시간으로 얼굴을 인식합니다.

실행 방법:
    python recognize.py

키 조작:
    q / ESC — 종료
"""

import os
import sys
import cv2
import pickle
import numpy as np
import face_recognition

# ── 설정 ─────────────────────────────────────────────────────
CAM_W, CAM_H    = 640, 480
PROCESS_SCALE   = 0.5     # 인식 처리용 축소 비율 (성능 향상)
PROCESS_EVERY   = 2       # N프레임마다 인식 실행
TOLERANCE       = 0.5     # 인식 임계값 (낮을수록 엄격, 0.4~0.6 권장)
UNKNOWN_LABEL   = "Unknown"

DATA_DIR      = os.path.join(os.path.dirname(__file__), "data")
ENCODINGS_BIN = os.path.join(DATA_DIR, "encodings.bin")

# ── 색상 (BGR) ───────────────────────────────────────────────
C_GREEN  = (60, 220, 60)
C_RED    = (60, 60, 220)
C_YELLOW = (0, 200, 220)
C_WHITE  = (255, 255, 255)
C_BLACK  = (0,   0,   0)
C_DARK   = (30,  30,  30)
C_GRAY   = (140, 140, 140)


# ── 인코딩 로드 ───────────────────────────────────────────────
def load_encodings():
    if not os.path.exists(ENCODINGS_BIN):
        print(f"[Error] {ENCODINGS_BIN} not found.")
        print("  Run collect_faces.py first to register faces.")
        sys.exit(1)

    with open(ENCODINGS_BIN, "rb") as f:
        data = pickle.load(f)

    encodings = data["encodings"]
    names     = data["names"]
    print(f"[Loaded] {len(encodings)} encodings  ({len(set(names))} person(s))")
    return encodings, names


# ── UI 헬퍼 ─────────────────────────────────────────────────
def put_text(frame, msg, pos, color=C_WHITE, scale=0.6, thick=2):
    cv2.putText(frame, msg, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, C_BLACK, thick + 2, cv2.LINE_AA)
    cv2.putText(frame, msg, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def draw_face_box(frame, top, right, bottom, left, name, confidence):
    color = C_GREEN if name != UNKNOWN_LABEL else C_RED

    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

    # 이름 + 신뢰도 라벨 배경
    label = f"{name}  {confidence:.0f}%" if name != UNKNOWN_LABEL else UNKNOWN_LABEL
    lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0]
    cv2.rectangle(frame, (left, bottom), (left + lw + 10, bottom + lh + 10), color, -1)
    cv2.putText(frame, label, (left + 5, bottom + lh + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_BLACK, 1, cv2.LINE_AA)


def draw_top_bar(frame, w, face_count):
    cv2.rectangle(frame, (0, 0), (w, 40), C_DARK, -1)
    msg = f"Face Recognizer  |  {face_count} face(s) detected  |  q=quit"
    put_text(frame, msg, (10, 28), C_WHITE, 0.52, 1)


# ── 인식 루프 ─────────────────────────────────────────────────
def run(known_encodings, known_names):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Cannot open camera.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

    frame_count  = 0
    face_results = []   # [(top, right, bottom, left, name, confidence), ...]

    print("[Running] Press q or ESC to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        _, w  = frame.shape[:2]

        # N프레임마다 인식 처리
        if frame_count % PROCESS_EVERY == 0:
            small = cv2.resize(frame, (0, 0), fx=PROCESS_SCALE, fy=PROCESS_SCALE)
            rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, locations)

            face_results = []
            for enc, loc in zip(encodings, locations):
                distances = face_recognition.face_distance(known_encodings, enc)

                if len(distances) == 0 or distances.min() > TOLERANCE:
                    name, confidence = UNKNOWN_LABEL, 0.0
                else:
                    best_idx    = int(np.argmin(distances))
                    name        = known_names[best_idx]
                    confidence  = (1 - distances[best_idx]) * 100

                # 좌표를 원본 프레임 크기로 복원
                top, right, bottom, left = [int(v / PROCESS_SCALE) for v in loc]
                face_results.append((top, right, bottom, left, name, confidence))

        # 결과 그리기
        for top, right, bottom, left, name, confidence in face_results:
            draw_face_box(frame, top, right, bottom, left, name, confidence)

        draw_top_bar(frame, w, len(face_results))

        cv2.imshow("Face Recognizer", frame)
        frame_count += 1

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Bye.")


def main():
    print("=" * 48)
    print("  Face Recognizer")
    print(f"  tolerance={TOLERANCE}  scale={PROCESS_SCALE}")
    print("=" * 48)
    known_encodings, known_names = load_encodings()
    run(known_encodings, known_names)


if __name__ == "__main__":
    main()
