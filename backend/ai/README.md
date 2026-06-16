# backend/ai — 비전 AI 라이브러리

얼굴 인식 · 객체 추적 · 포즈 추정 모듈 패키지.  
`vision/` 폴더의 테스트 파이프라인을 팀원이 import해서 쓸 수 있도록 라이브러리화한 버전.

---

## 패키지 구조

```
backend/ai/
├── face/
│   ├── face_db.py          # FaceDB — encodings.bin 로드
│   └── face_recognizer.py  # FaceRecognizer, FaceMatch
├── pose/
│   └── pose_estimator.py   # PoseEstimatorBase + 3개 모델 + compute_joint_angles
├── tracking/
│   └── byte_tracker.py     # ByteTrackTracker, TrackBox
└── __init__.py             # 전체 re-export
```

---

## 빠른 시작

```python
from backend.ai import FaceRecognizer, ByteTrackTracker, MediaPipePoseEstimator
```

또는 서브패키지 직접 import:

```python
from backend.ai.face import FaceRecognizer, FaceMatch
from backend.ai.pose import MediaPipePoseEstimator, compute_joint_angles
from backend.ai.tracking import ByteTrackTracker, TrackBox
```

---

## 얼굴 인식

### FaceDB

`encodings.bin` 파일을 로드합니다. `collect_faces.py`로 먼저 얼굴을 등록해야 합니다.

```python
from backend.ai.face import FaceDB

encodings, names = FaceDB.load()                        # ./data/encodings.bin
encodings, names = FaceDB.load("/path/to/encodings.bin") # 경로 지정
```

### FaceRecognizer

```python
from backend.ai.face import FaceRecognizer, FaceMatch

recognizer = FaceRecognizer(
    encodings_path=None,  # None → ./data/encodings.bin
    tolerance=0.5,        # 낮을수록 엄격 (권장: 0.4~0.6)
    scale=0.5,            # 처리 해상도 축소 비율 (성능 향상)
    model="hog",          # "hog"(CPU) 또는 "cnn"(GPU)
)

# 전체 프레임에서 인식 (여러 명 동시)
matches: list[FaceMatch] = recognizer.recognize(frame)
for m in matches:
    print(m.name, m.confidence)  # "홍길동", 87.3
    # m.top, m.right, m.bottom, m.left  → 얼굴 bbox

# 크롭 영역에서 인식 (이름 or None)
name: str | None = recognizer.recognize_crop(cropped_frame)
```

**FaceMatch 필드**

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | `str` | 인식된 이름 (`"Unknown"` = 미등록) |
| `confidence` | `float` | 신뢰도 0~100 |
| `top/right/bottom/left` | `int` | 얼굴 bbox (픽셀) |

---

## 객체 추적

### ByteTrackTracker

```python
from backend.ai.tracking import ByteTrackTracker, TrackBox

tracker = ByteTrackTracker(
    model_name="yolo11n.pt",  # YOLO 모델 (최초 실행 시 자동 다운로드)
    conf=0.3,                  # 검출 신뢰도
    classes=[0],               # [0] = person only, None = 전체
)

# 프레임별 스트리밍 (권장)
for frame, boxes in tracker.stream(source=0):  # 0=웹캠, 파일경로 가능
    for box in boxes:  # box: TrackBox
        print(box.id, box.x1, box.y1, box.x2, box.y2, box.conf)

# 독립 실행 데모
tracker.run(source=0)
```

**TrackBox 필드**

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | `int` | ByteTrack 고유 추적 ID |
| `x1, y1, x2, y2` | `int` | bbox 좌표 (픽셀) |
| `conf` | `float` | 검출 신뢰도 |

---

## 포즈 추정

세 모델 모두 **COCO-17 keypoints** `[(x, y, confidence), ...] × 17` 반환.

### 모델 선택

| 클래스 | 방식 | 속도 | 비고 |
|--------|------|------|------|
| `MediaPipePoseEstimator` | BlazePose (CPU) | 빠름 | 추가 설치 불필요 |
| `ViTPoseEstimator` | ViT + YOLO11n | 중간 | GPU 권장, ~330MB |
| `DETRPoseEstimator` | RTMDet + RTMPose | 균형 | mmpose 필요 |

### 단일 프레임 추정

```python
from backend.ai.pose import MediaPipePoseEstimator, compute_joint_angles
import cv2

estimator = MediaPipePoseEstimator()  # 또는 ViTPoseEstimator(), DETRPoseEstimator()

cap = cv2.VideoCapture(0)
ret, frame = cap.read()

keypoints = estimator.estimate(frame)
# → [(x, y, confidence), ...] × 17   or   None (미검출)

if keypoints:
    angles = compute_joint_angles(keypoints)
    print(angles["left_elbow"])   # 143.2 (도)
    print(angles["right_knee"])   # None (신뢰도 부족)
```

### COCO-17 키포인트 인덱스

| id | 이름 | id | 이름 |
|----|------|----|------|
| 0 | nose | 9 | left_wrist |
| 1 | left_eye | 10 | right_wrist |
| 2 | right_eye | 11 | left_hip |
| 3 | left_ear | 12 | right_hip |
| 4 | right_ear | 13 | left_knee |
| 5 | left_shoulder | 14 | right_knee |
| 6 | right_shoulder | 15 | left_ankle |
| 7 | left_elbow | 16 | right_ankle |
| 8 | right_elbow | | |

### 계산 가능한 관절 각도 (8개)

| 관절 | 기준점 A → 꼭짓점 → 기준점 B |
|------|-------------------------------|
| `left_elbow` | 왼어깨 → 왼팔꿈치 → 왼손목 |
| `right_elbow` | 오른어깨 → 오른팔꿈치 → 오른손목 |
| `left_shoulder` | 왼팔꿈치 → 왼어깨 → 왼엉덩이 |
| `right_shoulder` | 오른팔꿈치 → 오른어깨 → 오른엉덩이 |
| `left_hip` | 왼어깨 → 왼엉덩이 → 왼무릎 |
| `right_hip` | 오른어깨 → 오른엉덩이 → 오른무릎 |
| `left_knee` | 왼엉덩이 → 왼무릎 → 왼발목 |
| `right_knee` | 오른엉덩이 → 오른무릎 → 오른발목 |

### 라이브 데모 (JSON 자동 저장)

```python
estimator.run(source=0)
# 종료 시 mediapipe_20260609_143022.json 자동 저장
```

저장 JSON 구조:
```json
{
  "model": "mediapipe",
  "source": "0",
  "frames": [
    {
      "frame": 0,
      "keypoints": [
        {"id": 0, "name": "nose", "x": 320.5, "y": 215.3, "confidence": 0.99}
      ],
      "joint_angles": {
        "left_elbow": 143.27,
        "right_knee": null
      }
    }
  ]
}
```

### MediaPipePoseEstimator 모델 경로 지정

```python
# 기본: ./data/pose_landmarker_lite.task (없으면 자동 다운로드)
estimator = MediaPipePoseEstimator()

# 경로 직접 지정
estimator = MediaPipePoseEstimator(model_path="/path/to/pose_landmarker_lite.task")
```

---

## 의존 패키지

| 기능 | 패키지 |
|------|--------|
| 얼굴 인식 | `face-recognition` (dlib) |
| 객체 추적 | `ultralytics` (YOLO11 + ByteTrack) |
| MediaPipe | `mediapipe==0.10.9` |
| ViTPose | `transformers>=5.0`, `accelerate` |
| DETRPose | `openmim`, `mmengine`, `mmcv==2.1.0`, `mmdet`, `mmpose` |
| 공통 | `opencv-python`, `numpy` |

> **주의**: `mmcv==2.1.0`은 CUDA Toolkit과 버전이 일치해야 소스 빌드 가능.  
> `setuptools` 는 79.x 이하 사용 (`pkg_resources` 제거 문제).
