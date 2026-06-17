# backend/ai — 개발 컨텍스트

> **Claude Code 참조용 문서**
> 이 파일은 AI 어시스턴트가 이 모듈을 이해하고 이어서 개발할 수 있도록 설계 결정, 삽질 기록, 현재 상태를 기록한다.
> 사용법 문서는 README.md 참고.

---

## 모듈 목적과 위치

`backend/ai/`는 `vision/` 폴더에서 테스트·검증된 컴퓨터 비전 파이프라인을 백엔드에서 import해서 쓸 수 있도록 라이브러리화한 패키지다.

```
프로젝트 흐름:
  vision/       → 독립 테스트 환경 (웹캠 연결, 단독 실행)
  backend/ai/   → 라이브러리 (import해서 백엔드 로직에 통합)
  backend/      → FastAPI 백엔드 (ai/ 패키지를 여기서 사용)
```

`vision/lib/`과 `backend/ai/`는 거의 동일하되, `backend/ai/`는 경로 의존성을 제거해 어디서든 import 가능하도록 파라미터화했다.

---

## 패키지 구조 및 설계 결정

```
backend/ai/
├── face/           얼굴 인식 (face_recognition / dlib 기반)
├── pose/           포즈 추정 (3개 모델 공통 인터페이스)
├── tracking/       객체 추적 (YOLO11 + ByteTrack)
└── __init__.py     전체 re-export
```

### 왜 서브패키지로 나눴나?
백엔드에서 포즈만 쓰거나 추적만 쓰는 경우, 무거운 패키지(mmpose, mediapipe 등)를 전부 로드하지 않아도 되도록 분리했다. `from backend.ai.pose import MediaPipePoseEstimator`처럼 필요한 것만 import 가능.

### 공통 인터페이스 (PoseEstimatorBase)
세 포즈 모델(MediaPipe / ViTPose / DETRPose)은 모두 동일한 출력 형식을 갖는다:
```python
estimate(frame) → [(x, y, confidence), ...] × 17  or  None
```
COCO-17 keypoints 기준. 모델을 교체해도 downstream 코드 수정 없음.

---

## 환경 설정 — 반드시 읽을 것

### 가상환경
```bash
source backend/.venv/bin/activate   # uv로 관리
```

### CUDA / PyTorch 버전 (2026-06-09 기준)
- torch: `2.12.0+cu130` (CUDA 13.0 빌드)
- nvcc: `/usr/local/cuda-13.0/bin/nvcc` — PATH 등록 필요
- nvidia-smi CUDA 버전(드라이버)과 toolkit 버전은 다름. 빌드 시 nvcc 버전이 기준

```bash
# ~/.bashrc에 등록되어 있어야 함
export PATH=/usr/local/cuda-13.0/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-13.0/lib64:$LD_LIBRARY_PATH
```

### setuptools 버전 고정 — 절대 82+ 업그레이드 금지
```
setuptools==79.0.1  ← 이 버전 유지
```
setuptools 82+에서 `pkg_resources`가 제거됨. mmcv / mim 빌드가 `pkg_resources`에 의존하므로 업그레이드하면 mmcv 소스 빌드가 깨진다. `pip install --upgrade setuptools` 실행 금지.

---

## 패키지별 설치 기록 및 주의사항

### mmcv (가장 까다로운 패키지)
- **버전**: `mmcv==2.1.0` (2.2.0 사용 시 mmdet 3.3.0과 버전 충돌)
- **prebuilt wheel 없음**: cu130/torch2.12.0 조합의 prebuilt wheel이 없어 소스 빌드 필요
- **빌드 명령** (재설치 필요 시):
  ```bash
  pip install --no-build-isolation "mmcv==2.1.0" \
    -f https://download.openmmlab.com/mmcv/dist/cu130/torch2.12.0/index.html
  ```
  `--no-build-isolation` 필수 — isolated build env에서 pkg_resources를 못 찾음
- **빌드 시간**: 10~20분 (CUDA 커널 컴파일)

### mmdet / mmpose
```bash
pip install --no-build-isolation chumpy   # mmpose 의존성, 구버전 패키지
mim install mmdet mmpose                   # mmengine은 이미 설치됨
```
`chumpy`도 `--no-build-isolation` 필요 (setup.py에서 `import pip` 호출하는 구버전 버그).

### mediapipe
- 버전: `0.10.9`
- **`solutions` 모듈 없음** — Tasks API만 사용 가능
  ```python
  # ❌ 이렇게 하면 AttributeError
  import mediapipe as mp
  mp.solutions.pose
  
  # ✅ 올바른 방법
  from mediapipe.tasks import python
  from mediapipe.tasks.python import vision
  ```

### transformers (ViTPose)
- 버전: `5.x`
- **클래스명 변경됨**:
  ```python
  # ❌ 구버전
  ViTPoseForPoseEstimation
  
  # ✅ transformers 5.x
  VitPoseForPoseEstimation
  ```

### xtcocotools (mmpose 의존)
numpy 버전과 바이너리 불일치 문제 발생 시 재빌드:
```bash
pip install --force-reinstall --no-build-isolation --no-binary xtcocotools xtcocotools
```

---

## 모듈별 현재 상태 (2026-06-09)

### face/
| 클래스 | 상태 | 비고 |
|--------|------|------|
| `FaceDB` | ✅ 동작 확인 | `encodings.bin` 로드 |
| `FaceRecognizer` | ✅ 동작 확인 | fusion_track에서 검증 |

### tracking/
| 클래스 | 상태 | 비고 |
|--------|------|------|
| `ByteTrackTracker` | ✅ 동작 확인 | stream() / run() 모두 검증 |

### pose/
| 클래스 | 상태 | 비고 |
|--------|------|------|
| `MediaPipePoseEstimator` | ✅ 동작 확인 | JSON 저장, 각도 계산 검증 완료 |
| `ViTPoseEstimator` | ⏳ 미테스트 | 모델 ~330MB 첫 실행 시 다운로드 |
| `DETRPoseEstimator` | ⏳ 미테스트 | 설치 완료, 실행 테스트 필요 |
| `compute_joint_angles` | ✅ 동작 확인 | 8개 관절, conf_thr=0.0 기본값 |

---

## 데이터 파일 경로

`backend/ai/`는 경로를 파라미터로 받는다. 기본값은 실행 시점의 `./data/` 기준.

| 파일 | 기본 경로 | 생성 방법 |
|------|----------|-----------|
| `encodings.bin` | `./data/encodings.bin` | `vision/collect_faces.py` 실행 |
| `pose_landmarker_lite.task` | `./data/pose_landmarker_lite.task` | MediaPipe 첫 실행 시 자동 다운로드 |
| `yolo11n.pt` | 현재 디렉토리 | ultralytics 첫 실행 시 자동 다운로드 |
| ViTPose 모델 | HuggingFace 캐시 | 첫 실행 시 자동 다운로드 (~330MB) |
| RTMDet+RTMPose | mmpose 캐시 | 첫 실행 시 자동 다운로드 |

---

## JSON 출력 형식

`PoseEstimatorBase.run()` 종료 시 자동 저장:
- **파일명**: `{model}_{YYYYMMDD_HHMMSS}.json` (예: `mediapipe_20260609_143022.json`)
- **저장 위치**: 스크립트 실행 경로 기준

```json
{
  "model": "mediapipe",
  "source": "0",
  "frames": [
    {
      "frame": 0,
      "keypoints": [
        {"id": 5, "name": "left_shoulder", "x": 280.1, "y": 310.2, "confidence": 0.97}
      ],
      "joint_angles": {
        "left_elbow": 143.27,
        "right_knee": null
      }
    }
  ]
}
```

`null`은 해당 관절을 구성하는 키포인트 신뢰도가 `conf_thr` 미만임을 의미.

---

## 앞으로 개발할 것들

- [ ] `ViTPoseEstimator`, `DETRPoseEstimator` 실행 테스트
- [ ] 세 모델 포즈 성능 비교 (정확도 / FPS)
- [ ] 정답 영상 ↔ 촬영 영상 자세 비교 구현
  - `vision/fusion_track2.py`로 정규화 키포인트(`x_norm`, `y_norm`) 추출
  - 프레임별 관절 각도 차이로 유사도 점수 계산
- [ ] 필터링 (성능 부족 시)
  - 키포인트: One Euro Filter
  - 스케일: EMA
