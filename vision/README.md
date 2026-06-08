# Vision 파이프라인

`backend/` 가상환경(uv)을 공유하되 다른 폴더와 독립 실행되는 테스트 파이프라인입니다.  
최종 목표: 각 모듈을 **class 형태**로 팀원이 import해서 사용할 수 있도록 제공.

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
├── collect_faces.py     # 얼굴 데이터 수집 + 인코딩 학습
├── recognize.py         # 실시간 얼굴 인식
├── tracking.py          # ByteTrack / SAM 비교 테스트 (참고용)
├── final_track.py       # ByteTrack 단독 추적 (확정본)
├── fusion_track.py      # 얼굴인식 + ByteTrack 융합 추적
├── pose_est.py          # Pose Estimation (MediaPipe / ViTPose / DETRPose)
└── data/
    ├── faces/                      # 수집된 얼굴 이미지
    ├── users.json                  # {user_id: username}
    ├── encodings.bin               # face_recognition 인코딩
    └── pose_landmarker_lite.task   # MediaPipe 모델 (자동 다운로드)
```

---

## 모듈별 설명

### 1. `collect_faces.py` — 얼굴 수집

웹캠으로 얼굴 40장 수집 → `face_recognition` 128-d 인코딩 생성 → `data/encodings.bin` 저장

```bash
python collect_faces.py
# r: 새 얼굴 등록 | q/ESC: 종료
```

### 2. `recognize.py` — 얼굴 인식

`encodings.bin` 로드 → 웹캠 실시간 얼굴 인식 및 이름 표시

```bash
python recognize.py
```

### 3. `final_track.py` — ByteTrack 추적

YOLO11n + ByteTrack 다중 객체 추적

```bash
python final_track.py
python final_track.py --source video.mp4 --conf 0.4
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--source` | `0` | 웹캠(0) 또는 파일 경로 |
| `--conf` | `0.3` | 검출 신뢰도 임계값 |
| `--model` | `yolo11n.pt` | YOLO 모델 |

### 4. `fusion_track.py` — 얼굴인식 + ByteTrack 융합

**상태 머신:**

```
SEARCHING  →  face_recognition 실행, 등록된 얼굴 최초 인식 시 TRACKING 전환
TRACKING   →  face_recognition 완전 종료, 해당 1인 bbox만 추적
타겟 소멸  →  자동으로 SEARCHING 재전환 (seen_ids 초기화)
```

```bash
python fusion_track.py
python fusion_track.py --source video.mp4 --tolerance 0.45
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--source` | `0` | 웹캠 또는 파일 |
| `--conf` | `0.4` | YOLO 신뢰도 |
| `--face-interval` | `15` | SEARCHING 중 재인식 주기 (프레임) |
| `--tolerance` | `0.5` | 얼굴 인식 임계값 (낮을수록 엄격) |

> `collect_faces.py`로 얼굴 등록 선행 필요

### 5. `pose_est.py` — Pose Estimation

세 모델 모두 **COCO-17 keypoints** 출력, 공통 스켈레톤 시각화  
웹캠 30fps 고정

```bash
python pose_est.py --model mediapipe   # 즉시 실행 가능
python pose_est.py --model vitpose     # 첫 실행 시 ~330MB 다운로드
python pose_est.py --model detrpose    # CUDA Toolkit 설치 후 사용 가능
python pose_est.py --model mediapipe --source video.mp4
```

| 모델 | 방식 | 속도 | 상태 |
|------|------|------|------|
| `mediapipe` | BlazePose Tasks API (33→17 매핑) | 빠름 | ✅ |
| `vitpose` | ViT + YOLO11n 사람 검출 | 중간 (GPU 권장) | ✅ |
| `detrpose` | RTMDet + RTMPose (mmpose) | 균형 | ⏳ CUDA Toolkit 필요 |

---

## 설치된 패키지 (backend venv)

```
opencv-contrib-python    웹캠 / 이미지 처리
numpy                    행렬 연산
face-recognition         dlib 기반 128-d 얼굴 인코딩
pillow                   이미지 변환
ultralytics              YOLO11 + ByteTrack
mediapipe 0.10.9         BlazePose Tasks API
transformers 5.x         VitPoseForPoseEstimation
accelerate               HuggingFace 모델 가속
openmim                  mmpose 설치 도구 (준비됨)
```

### DETRPose 활성화 (CUDA Toolkit 설치 후)

```bash
# CUDA Toolkit 설치 (nvcc 필요)
sudo apt install cuda-toolkit-13-0

# mmpose 스택 설치
mim install mmengine "mmcv>=2.0.0" mmdet mmpose

# 실행
python pose_est.py --model detrpose
```

---

## 공통 클래스 인터페이스

```python
# ByteTrack
from final_track import ByteTrackTracker
tracker = ByteTrackTracker(conf=0.3)
tracker.run(source=0)

# 얼굴인식 + 추적 융합
from fusion_track import FusionTracker
tracker = FusionTracker(conf=0.4, tolerance=0.5)
tracker.run(source=0)

# Pose Estimation (단일 프레임)
from pose_est import MediaPipePoseEstimator, ViTPoseEstimator
estimator = MediaPipePoseEstimator()
keypoints = estimator.estimate(frame)
# → [(x, y, confidence), ...] × 17   or   None

# 라이브 데모
estimator.run(source=0)
```

---

## 이미지 필터링 (미구현 — 포즈 테스트 후 필요시 추가)

pose estimation 모델 자체 성능이 충분하면 생략 가능. 필요 시 아래 결론 기준으로 구현.

| 대상 | 필터 | 이유 |
|------|------|------|
| 포즈 키포인트 (x, y) | **One Euro Filter** | 정지↔빠른동작 전환 시 래그·노이즈 동시 제어. MediaPipe 내부 방식 |
| 스케일 비율 | **EMA** | 완만한 값 변화에 경량 지수 평균으로 충분 |
| bbox 위치 | 추가 필터 불필요 | ByteTrack 내부 칼만이 이미 처리 |

---

## 다음 작업 예정

- [ ] DETRPose 활성화 (`sudo apt install cuda-toolkit-13-0` 후)
- [ ] 세 모델 포즈 성능 비교 테스트
- [ ] 필터링 구현 (One Euro / EMA) — 포즈 키포인트 노이즈 제거
- [ ] 정답 영상 ↔ 촬영 영상 스케일 정규화
- [ ] 각 모듈 최종 class화 및 팀 배포
