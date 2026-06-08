"""
얼굴 데이터 수집 + 인코딩 학습 스크립트 (독립 실행용)

화면 중앙 가이드 박스 안에 얼굴이 들어와야만 캡쳐됩니다.
수집 완료 후 face_recognition 라이브러리로 128-d 인코딩을 생성하여
data/encodings.pkl 에 저장합니다.

실행 방법:
    python collect_faces.py

필요 패키지:
    uv pip install opencv-contrib-python face_recognition

저장 경로:
    data/faces/<id>_NNN.png    — 컬러 얼굴 이미지 (패딩 포함)
    data/users.json            — {user_id: username}
    data/encodings.pkl         — {encodings: [...], ids: [...], names: [...]}

키 조작:
    r       — 새 얼굴 등록
    q / ESC — 종료

─────────────────────────────────────────────────────────────
TODO: 얼굴 상하좌우 회전 강제 기능 (나중에 추가)

필요 라이브러리:
    mediapipe==0.10.9          # 0.10.10 이상은 solutions API 제거됨

핵심 기법:
    1. mp.solutions.face_mesh 로 468개 랜드마크 추출
    2. 코끝(1), 턱(152), 눈끝(33, 263), 입꼬리(57, 287) 6점 선택
    3. cv2.solvePnP() 로 3D 회전 벡터 → yaw / pitch 각도 계산
    4. 단계별 허용 범위: FORWARD(±12°), LEFT(yaw>18°), RIGHT(yaw<-18°),
       UP(pitch>12°), DOWN(pitch<-12°) 조건 불만족 시 캡쳐 차단

참고:
    MediaPipe Face Mesh 공식 문서
      https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker
    Head Pose Estimation with OpenCV & solvePnP
      https://github.com/niconielsen32/ComputerVision/tree/master/headPoseEstimation
    랜드마크 인덱스 시각화
      https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
─────────────────────────────────────────────────────────────
"""

import os
import sys
import cv2
import json
import time
import pickle

import face_recognition

# ── 설정 ─────────────────────────────────────────────────────
CAM_W, CAM_H     = 640, 480
SAMPLES_NEEDED   = 40
CAPTURE_INTERVAL = 0.2
GUIDE_W_RATIO    = 0.38
GUIDE_H_RATIO    = 0.60
MIN_FACE_RATIO   = 0.25
FACE_PADDING     = 0.3    # 얼굴 크롭 시 여백 비율 (face_recognition 검출용)

DATA_DIR      = os.path.join(os.path.dirname(__file__), "data")
FACES_DIR     = os.path.join(DATA_DIR, "faces")
USERS_JSON    = os.path.join(DATA_DIR, "users.json")
ENCODINGS_PKL = os.path.join(DATA_DIR, "encodings.bin")

# ── 색상 (BGR) ───────────────────────────────────────────────
C_GREEN  = (60, 220, 60)
C_RED    = (60, 60, 220)
C_YELLOW = (0, 200, 220)
C_BLUE   = (220, 160, 60)
C_WHITE  = (255, 255, 255)
C_BLACK  = (0,   0,   0)
C_DARK   = (30,  30,  30)
C_GRAY   = (140, 140, 140)

# ── 유저 DB ──────────────────────────────────────────────────
def load_users():
    if os.path.exists(USERS_JSON):
        with open(USERS_JSON) as f:
            return json.load(f)
    return {}


def save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_JSON, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def next_user_id(users):
    if not users:
        return 1
    return max(int(k) for k in users) + 1


# ── 인코딩 학습 ───────────────────────────────────────────────
def encode_faces():
    """data/faces/ 의 모든 이미지를 face_recognition으로 인코딩하여 저장."""
    users = load_users()
    encodings, ids, names = [], [], []
    image_files = sorted(f for f in os.listdir(FACES_DIR) if f.endswith(".png"))

    print(f"\n  Encoding {len(image_files)} images...")
    for fname in image_files:
        user_id = fname.split("_")[0]
        username = users.get(user_id, f"user_{user_id}")
        img = face_recognition.load_image_file(os.path.join(FACES_DIR, fname))
        encs = face_recognition.face_encodings(img)
        if encs:
            encodings.append(encs[0])
            ids.append(user_id)
            names.append(username)

    with open(ENCODINGS_PKL, "wb") as f:
        pickle.dump({"encodings": encodings, "ids": ids, "names": names}, f)

    print(f"  Saved {len(encodings)} encodings → data/encodings.bin")
    return len(encodings)


# ── 얼굴 검출 ────────────────────────────────────────────────
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)


def detect_faces(gray):
    return face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )


def face_in_guide(bbox, gx1, gy1, gx2, gy2):
    fx, fy, fw, fh = bbox
    cx, cy = fx + fw // 2, fy + fh // 2
    in_box  = gx1 < cx < gx2 and gy1 < cy < gy2
    size_ok = (fw >= (gx2 - gx1) * MIN_FACE_RATIO and
               fh >= (gy2 - gy1) * MIN_FACE_RATIO)
    return in_box and size_ok


def crop_face_with_padding(frame, bbox):
    """패딩을 포함한 컬러 얼굴 이미지 반환 (face_recognition 재검출용)."""
    h, w = frame.shape[:2]
    fx, fy, fw, fh = bbox
    pad_x = int(fw * FACE_PADDING)
    pad_y = int(fh * FACE_PADDING)
    x1 = max(0, fx - pad_x)
    y1 = max(0, fy - pad_y)
    x2 = min(w, fx + fw + pad_x)
    y2 = min(h, fy + fh + pad_y)
    return frame[y1:y2, x1:x2]


# ── UI 헬퍼 ─────────────────────────────────────────────────
def put_text(frame, msg, pos, color=C_WHITE, scale=0.6, thick=2):
    cv2.putText(frame, msg, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, C_BLACK, thick + 2, cv2.LINE_AA)
    cv2.putText(frame, msg, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def draw_guide_box(frame, gx1, gy1, gx2, gy2, color, label=""):
    r, t = 18, 3
    cv2.ellipse(frame, (gx1+r, gy1+r), (r,r), 180, 0, 90, color, t)
    cv2.ellipse(frame, (gx2-r, gy1+r), (r,r), 270, 0, 90, color, t)
    cv2.ellipse(frame, (gx2-r, gy2-r), (r,r),   0, 0, 90, color, t)
    cv2.ellipse(frame, (gx1+r, gy2-r), (r,r),  90, 0, 90, color, t)
    cv2.line(frame, (gx1+r, gy1), (gx2-r, gy1), color, t)
    cv2.line(frame, (gx1+r, gy2), (gx2-r, gy2), color, t)
    cv2.line(frame, (gx1, gy1+r), (gx1, gy2-r), color, t)
    cv2.line(frame, (gx2, gy1+r), (gx2, gy2-r), color, t)
    if label:
        lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)[0]
        put_text(frame, label,
                 ((gx1+gx2)//2 - lw//2, gy2+lh+8), color, 0.52, 1)


def draw_top_bar(frame, msg, w):
    cv2.rectangle(frame, (0, 0), (w, 40), C_DARK, -1)
    put_text(frame, msg, (10, 28), C_WHITE, 0.55, 1)


def draw_progress_bar(frame, count, total, h, w):
    bx1, bx2 = 20, w - 20
    by1, by2 = h - 28, h - 12
    filled = int((count / total) * (bx2 - bx1))
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), C_GRAY, -1)
    if filled > 0:
        cv2.rectangle(frame, (bx1, by1), (bx1+filled, by2), C_GREEN, -1)
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), C_WHITE, 1)
    pct = f"{count}/{total}"
    pw, _ = cv2.getTextSize(pct, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
    put_text(frame, pct, (w//2 - pw//2, by2-2), C_WHITE, 0.45, 1)


def draw_encoding_screen(cap, w, h):
    """인코딩 중 대기 화면."""
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), C_DARK, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        msg = "Encoding faces..."
        mw, _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        put_text(frame, msg, (w//2 - mw//2, h//2), C_YELLOW, 0.8, 2)
        cv2.imshow("Face Collector", frame)
        cv2.waitKey(1)


# ── 수집 루프 ─────────────────────────────────────────────────
def collect_samples(cap, username):
    users   = load_users()
    user_id = next_user_id(users)
    users[str(user_id)] = username
    save_users(users)
    os.makedirs(FACES_DIR, exist_ok=True)

    count    = 0
    last_cap = 0

    print(f"\n[Start] '{username}' (id={user_id})  —  {SAMPLES_NEEDED} samples")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        gw  = int(w * GUIDE_W_RATIO);  gh  = int(h * GUIDE_H_RATIO)
        gx1 = (w - gw) // 2;           gx2 = gx1 + gw
        gy1 = (h - gh) // 2;           gy2 = gy1 + gh

        faces = detect_faces(gray)
        valid = [f for f in faces if face_in_guide(f, gx1, gy1, gx2, gy2)]

        now = time.time()
        if len(valid) == 1 and now - last_cap >= CAPTURE_INTERVAL:
            # BGR → RGB 컬러 이미지를 패딩 포함하여 저장
            face_img = crop_face_with_padding(frame, valid[0])
            face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            path = os.path.join(FACES_DIR, f"{user_id}_{count:03d}.png")
            cv2.imwrite(path, cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR))
            count   += 1
            last_cap = now

        if len(faces) == 0:
            guide_color, status_msg = C_YELLOW, "No face detected"
        elif len(valid) == 0:
            guide_color, status_msg = C_RED,    "Move face into the box"
        elif len(valid) > 1:
            guide_color, status_msg = C_YELLOW, "One face only"
        else:
            guide_color, status_msg = C_GREEN,  f"Collecting...  {count}/{SAMPLES_NEEDED}"

        overlay = frame.copy()
        cv2.rectangle(overlay, (gx1, gy1), (gx2, gy2),
                      tuple(c//6 for c in guide_color), -1)
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

        for (fx, fy, fw, fh) in faces:
            col = C_GREEN if face_in_guide((fx,fy,fw,fh), gx1,gy1,gx2,gy2) else C_RED
            cv2.rectangle(frame, (fx,fy), (fx+fw,fy+fh), col, 2)

        draw_guide_box(frame, gx1, gy1, gx2, gy2, guide_color, status_msg)
        cxg, cyg = (gx1+gx2)//2, (gy1+gy2)//2
        cv2.line(frame, (cxg-10,cyg), (cxg+10,cyg), guide_color, 1)
        cv2.line(frame, (cxg,cyg-10), (cxg,cyg+10), guide_color, 1)

        draw_top_bar(frame, f"COLLECTING  |  {username}  |  q=cancel", w)
        draw_progress_bar(frame, count, SAMPLES_NEEDED, h, w)

        cv2.imshow("Face Collector", frame)
        key = cv2.waitKey(1) & 0xFF

        if key in (27, ord('q')):
            users_cur = load_users()
            users_cur.pop(str(user_id), None)
            save_users(users_cur)
            for i in range(count):
                p = os.path.join(FACES_DIR, f"{user_id}_{i:03d}.png")
                if os.path.exists(p): os.remove(p)
            print("[Cancelled]")
            return False

        if count >= SAMPLES_NEEDED:
            break

    # 인코딩 학습
    print(f"[Collected] {count} images saved. Encoding...")
    draw_encoding_screen(cap, w, h)
    n = encode_faces()
    print(f"[Done] '{username}' registered  ({n} total encodings in encodings.pkl)\n")
    return True


# ── 대기 화면 ─────────────────────────────────────────────────
def preview_loop(cap):
    print("\n[Idle] r = register  |  q/ESC = quit")
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        _, w  = frame.shape[:2]

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detect_faces(gray)
        for (fx, fy, fw, fh) in faces:
            cv2.rectangle(frame, (fx,fy), (fx+fw,fy+fh), C_BLUE, 2)

        draw_top_bar(frame, "Face Collector  |  r=register  |  q=quit", w)

        users = load_users()
        if users:
            put_text(frame, "Registered:", (10, 70), C_GRAY, 0.5, 1)
            for i, (uid, uname) in enumerate(sorted(users.items())):
                put_text(frame, f"  #{uid}  {uname}", (10, 95+i*22), C_WHITE, 0.5, 1)
        else:
            put_text(frame, "No users yet. Press r to register.",
                     (10, 70), C_YELLOW, 0.5, 1)

        cv2.imshow("Face Collector", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')): return False
        if key == ord('r'):       return True


def get_username():
    while True:
        name = input("Enter name (empty to cancel): ").strip()
        if not name: return None
        if len(name) > 30:
            print("  Too long (max 30 chars).")
            continue
        return name


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Cannot open camera.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

    print("=" * 52)
    print("  Face Collector  (face_recognition backend)")
    print("  40 samples → encodings.pkl")
    print("  r = register  |  q/ESC = quit")
    print("=" * 52)

    while True:
        if not preview_loop(cap): break
        cv2.destroyWindow("Face Collector")
        username = get_username()
        if not username: continue
        collect_samples(cap, username)

    cap.release()
    cv2.destroyAllWindows()
    print("Bye.")


if __name__ == "__main__":
    main()
