# Vision 파이프라인

`backend/` 가상환경(uv)을 공유하되 다른 폴더와 독립 실행되는 테스트 파이프라인입니다.

---

## 실행 환경

```bash
# 방법 1: venv 직접 활성화 후 실행
source backend/.venv/bin/activate
cd vision && python <파일>.py

# 방법 2: uv run (backend 폴더에서)
cd backend && uv run python ../vision/<파일>.py
```

---

## 파일 구조

```
vision/
├── lib/                        # 팀원 import용 라이브러리 패키지
│   ├── __init__.py
│   ├── face_db.py              # FaceDB — encodings.bin 로드
│   ├── face_recognizer.py      # FaceRecognizer, FaceMatch
│   ├── byte_tracker.py         # ByteTrackTracker, TrackBox
│   └── pose_estimator.py       # PoseEstimatorBase + 3개 모델 + compute_joint_angles
│
├── collect_faces.py            # 얼굴 데이터 수집 + 인코딩 학습 (독립 UI)
├── recognize.py                # 실시간 얼굴 인식 데모
├── tracking.py                 # ByteTrack / SAM 비교 테스트 (참고용)
├── final_track.py              # ByteTrack 단독 추적 CLI
├── fusion_track.py             # 얼굴인식 + ByteTrack 융합 (원본)
├── fusion_track2.py            # 얼굴인식 + ByteTrack + Pose 융합 (lib 버전)
├── pose_est.py                 # Pose Estimation CLI
└── data/
    ├── faces/                  # 수집된 얼굴 이미지
    ├── users.json              # {user_id: username}
    ├── encodings.bin           # face_recognition 인코딩
    └── pose_landmarker_lite.task   # MediaPipe 모델 (자동 다운로드)
```

---

## 파일별 실행 명령어

### collect_faces.py — 얼굴 데이터 수집 및 인코딩 저장

```bash
python collect_faces.py
```

- 웹캠으로 얼굴 수집 후 `data/encodings.bin` 저장
- `r` : 새 얼굴 등록 / `q`, `ESC` : 종료
- **recognize.py, fusion_track*.py 실행 전 반드시 먼저 실행**

---

### recognize.py — 실시간 얼굴 인식

```bash
python recognize.py
```

---

### tracking.py — 객체 추적 비교 테스트 (참고용)

```bash
python tracking.py --method bytetrack
python tracking.py --method sam
python tracking.py --method bytetrack --source video.mp4
python tracking.py --method bytetrack --conf 0.4
```

---

### final_track.py — YOLO11 + ByteTrack 다중 객체 추적

```bash
python final_track.py
python final_track.py --source video.mp4
python final_track.py --conf 0.4
```

---

### fusion_track.py — 얼굴 인식 + ByteTrack 융합 추적 (원본)

```bash
python fusion_track.py
python fusion_track.py --source video.mp4
python fusion_track.py --tolerance 0.45 --face-interval 10
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--source` | `0` | 웹캠 또는 파일 |
| `--conf` | `0.4` | YOLO 신뢰도 |
| `--face-interval` | `15` | SEARCHING 중 재인식 주기 (프레임) |
| `--tolerance` | `0.5` | 얼굴 인식 임계값 (낮을수록 엄격) |

---

### fusion_track2.py — 얼굴 인식 + ByteTrack + Pose Estimation 융합 (lib 버전)

타겟 bbox를 crop해 포즈 추정 → bbox 크기로 정규화 (`x_norm`, `y_norm` ∈ 0~1)  
→ 화면 어디에 있어도 동일한 자세 기준 좌표

```bash
# 추적만 (포즈 없음)
python fusion_track2.py

# 포즈 추정 포함
python fusion_track2.py --pose mediapipe
python fusion_track2.py --pose vitpose --source video.mp4

# 정규화 키포인트 + 관절 각도 JSON 저장
python fusion_track2.py --pose mediapipe --save-json output.json
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--pose` | `None` | 포즈 모델 (`mediapipe` / `vitpose` / `detrpose`) |
| `--save-json` | `None` | 정규화 키포인트 저장 경로 (`--pose` 필요) |
| `--source` | `0` | 웹캠 또는 파일 |
| `--conf` | `0.4` | YOLO 신뢰도 |
| `--tolerance` | `0.5` | 얼굴 인식 임계값 |
| `--face-interval` | `15` | SEARCHING 중 재인식 주기 |
| `--encodings` | `data/encodings.bin` | encodings.bin 경로 |

**저장 JSON 구조:**
```json
{
  "frame": 42,
  "bbox": {"x1": 120, "y1": 50, "x2": 320, "y2": 480},
  "keypoints": [
    {"id": 5, "name": "left_shoulder", "x_norm": 0.42, "y_norm": 0.18, "confidence": 0.97}
  ],
  "joint_angles": {"left_elbow": 143.2, "right_knee": null, ...}
}
```

---

### pose_est.py — Pose Estimation 3종 비교

```bash
python pose_est.py --model mediapipe
python pose_est.py --model vitpose
python pose_est.py --model detrpose
python pose_est.py --model mediapipe --source video.mp4
python pose_est.py --model mediapipe --save-json output.json
python pose_est.py --model mediapipe --save-json output.json --angle-conf 0.3
```

| 모델 | 방식 | 속도 | 상태 |
|------|------|------|------|
| `mediapipe` | BlazePose Tasks API (33→17 매핑) | 빠름 | ✅ |
| `vitpose` | ViT + YOLO11n 사람 검출 | 중간 (GPU 권장) | ✅ |
| `detrpose` | RTMDet + RTMPose (mmpose) | 균형 | ✅ |

---

## lib/ 패키지 — 팀원 import 가이드

```python
from lib import FaceRecognizer, ByteTrackTracker, MediaPipePoseEstimator
from lib import FaceDB, TrackBox, FaceMatch, compute_joint_angles

# 얼굴 인식기
recognizer = FaceRecognizer(tolerance=0.5)
matches = recognizer.recognize(frame)         # list[FaceMatch]
name    = recognizer.recognize_crop(crop)     # str | None

# ByteTrack 추적기
tracker = ByteTrackTracker(conf=0.3, classes=[0])
tracker.run(source=0)                         # 독립 실행
for frame, boxes in tracker.stream(source=0): # 프레임별 처리
    for box in boxes:  # box: TrackBox(id, x1, y1, x2, y2, conf)
        ...

# Pose Estimation (단일 프레임)
estimator = MediaPipePoseEstimator()
keypoints = estimator.estimate(frame)
# → [(x, y, confidence), ...] × 17   or   None

# 관절 각도 계산
angles = compute_joint_angles(keypoints)
# → {"left_elbow": 143.2, "right_knee": None, ...}
```

---

## 설치된 패키지 (backend venv)

```
opencv-contrib-python    웹캠 / 이미지 처리
numpy                    행렬 연산
face-recognition         dlib 기반 128-d 얼굴 인코딩
pillow                   이미지 변환
ultralytics              YOLO11 + ByteTrack
mediapipe 0.10.9         BlazePose Tasks API (solutions 없음)
transformers 5.x         VitPoseForPoseEstimation
accelerate               HuggingFace 모델 가속
openmim                  mmpose 설치 도구
mmengine 0.10.7
mmcv 2.1.0               소스 빌드 (cu130/torch2.12.0)
mmdet 3.3.0
mmpose 1.3.2
setuptools 79.0.1        82+ 사용 금지 (pkg_resources 제거됨)
```

---

## 이미지 필터링 (미구현 — 포즈 테스트 후 필요시 추가)

| 대상 | 필터 | 이유 |
|------|------|------|
| 포즈 키포인트 (x, y) | **One Euro Filter** | 정지↔빠른동작 전환 시 래그·노이즈 동시 제어 |
| 스케일 비율 | **EMA** | 완만한 값 변화에 경량 지수 평균으로 충분 |
| bbox 위치 | 추가 필터 불필요 | ByteTrack 내부 칼만이 이미 처리 |

---

## 다음 작업 예정

- [ ] `vitpose`, `detrpose` 실행 테스트
- [ ] 세 모델 포즈 성능 비교 (정확도 / FPS)
- [ ] 필터링 구현 (One Euro / EMA)
- [ ] 정답 영상 ↔ 촬영 영상 자세 비교 (정규화 좌표 기반)
