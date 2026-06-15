# Plank RAG Pipeline

플랭크 자세를 분석해 한국어 코멘트를 생성하는 RAG(Retrieval-Augmented Generation) 파이프라인.

> **요약**: 정규화 ViTPose JSON → ChromaDB 검색 → 라벨 타임라인 → Gemini 호출 → 자연어 피드백.

---

## 목차
1. [큰 그림](#큰-그림)
2. [파일 구성](#파일-구성)
3. [실행 방법](#실행-방법)
4. [테스트 절차](#테스트-절차)
5. [단계별 데이터 변환 예시](#단계별-데이터-변환-예시)
6. [환경변수](#환경변수)
7. [알려진 한계 & 후속 작업](#알려진-한계--후속-작업)

---

## 큰 그림

```
                          (1) JSON 입력
                                │
                                ▼
        ┌──────────────────────────────────────────┐
        │  loader.py                               │
        │   - JSON 파싱                              │
        │   - 프레임 단위로 FrameSample 생성             │
        └──────────────────────────────────────────┘
                                │  Iterable[FrameSample]
                                ▼
        ┌──────────────────────────────────────────┐
        │  vectorize.py                            │
        │   - COCO-17 (x, y) 평탄화 → 34차원 벡터       │
        └──────────────────────────────────────────┘
                                │  list[float] (34)
                                ▼
        ┌──────────────────────────────────────────┐
        │  store.py + ChromaDB                     │
        │   - 사전 적재된 데이터셋(answer/wrong 라벨)에서 │
        │     cosine 유사도 top-k 검색                  │
        └──────────────────────────────────────────┘
                                │  k개의 이웃 + 거리
                                ▼
        ┌──────────────────────────────────────────┐
        │  retriever.py                            │
        │   - 거리 가중 다수결로 프레임 라벨 결정          │
        │   - 같은 라벨 연속 구간을 segment 로 압축        │
        │   - 5프레임 미만 segment 는 양옆으로 흡수        │
        └──────────────────────────────────────────┘
                                │  RetrievalResult
                                ▼
        ┌──────────────────────────────────────────┐
        │  prompt.py                               │
        │   - 코치 페르소나 system prompt              │
        │   - 검색 타임라인을 user prompt 로 직렬화      │
        └──────────────────────────────────────────┘
                                │  GeminiPrompt
                                ▼
        ┌──────────────────────────────────────────┐
        │  llm.py                                  │
        │   - Gemini 2.5 Flash 호출                  │
        │   - 지수 backoff 재시도                      │
        └──────────────────────────────────────────┘
                                │  LlmResponse
                                ▼
                       (2) 한국어 마크다운 코멘트
```

(1) 사용자 영상에서 추출한 정규화 ViTPose JSON 1개 → (2) "## 전체 요약 / ## 구간별 평가 / ## 핵심 개선 포인트" 형식의 한국어 코멘트.

---

## 파일 구성

| 파일 | 역할 |
|---|---|
| `loader.py` | 정규화 JSON 파싱, COCO-17 관절 순서 정의, 프레임 단위 `FrameSample` 생성 |
| `vectorize.py` | `FrameSample` → 34차원 (x, y) 벡터 |
| `store.py` | 영속 ChromaDB 클라이언트 (cosine 거리, `data/vectordb/chroma/` 에 저장) |
| `ingest.py` | 라벨된 데이터셋을 ChromaDB 에 일괄 적재하는 CLI |
| `retriever.py` | 검색 + 거리 가중 투표 + segment 타임라인 생성 |
| `query.py` | 검색기만 단독 실행하는 CLI (Gemini 호출 X) |
| `prompt.py` | 시스템/사용자 프롬프트 빌더 (코치 페르소나, 출력 형식 고정) |
| `llm.py` | Gemini 호출 래퍼, API 키 로드, 재시도 |
| `pipeline.py` | 전체 파이프라인 통합 CLI |

---

## 실행 방법

### 0) 사전 준비

```bash
cd backend
uv sync                                  # 의존성 설치 (google-genai, chromadb 포함)
cp .env.example .env                     # 없다면
# .env 에 GEMINI_API_KEY 채우기 (https://aistudio.google.com/apikey)
```

### 1) 벡터DB 적재 (최초 1회 + 데이터 갱신 시)

```bash
uv run python -m ai.rag.ingest --reset
```

`data/result/output/vitpose_normalized/{answer,wrong}/*.json` 를 읽어 ChromaDB 에 적재.
약 8,900 프레임 (정자세 12 + 오자세 11 영상).

### 2) 검색기만 단독 실행 (Gemini 호출 없음, 비용 0)

```bash
uv run python -m ai.rag.query "<query.json 경로>"
uv run python -m ai.rag.query "<query.json>" --top-k 7 --min-segment 3
```

타임라인 segment 까지만 콘솔에 출력. LLM 단계 디버깅에 유용.

### 3) 전체 파이프라인 (Gemini 호출)

```bash
uv run python -m ai.rag.pipeline "<query.json 경로>"
uv run python -m ai.rag.pipeline "<query.json>" --top-k 7 --min-segment 3 --model gemini-2.5-pro
uv run python -m ai.rag.pipeline "<query.json>" --skip-llm   # 프롬프트까지만 출력
```

---

## 테스트 절차

### A. 형식·동작 확인 (빠름)
1. 정자세 파일과 오자세 파일을 각각 한 개씩 검색기에 통과시켜본다.
   ```bash
   uv run python -m ai.rag.query "C:\project\posefit\data\result\output\vitpose_normalized\answer\plank_true_5.json"
   uv run python -m ai.rag.query "C:\project\posefit\data\result\output\vitpose_normalized\wrong\plank_false_3.json"
   ```
   - 기대: 각각 `correct`, `wrong` 으로 분류됨. 타임라인 segment 가 너무 잘게 쪼개지지 않음.

2. 전체 파이프라인을 같은 파일들로 실행해 Gemini 출력 형식을 확인.
   ```bash
   uv run python -m ai.rag.pipeline "<위와 같은 파일>"
   ```
   - 기대: 응답이 `## 전체 요약 / ## 구간별 평가 / ## 핵심 개선 포인트` 마크다운으로 옴.
   - `correct` 100% 일 때는 마지막 섹션이 생략됨.

### B. 의미 있는 정확도 측정 (self-match 회피)
모든 학습 데이터는 이미 DB 에 있으니 데이터 파일을 그대로 쿼리로 쓰면 100% self-match 가 된다.

- **옵션 1 — 임시 보류(holdout)**: 평가하려는 영상을 잠시 폴더 밖으로 옮긴 뒤 `--reset` 으로 재적재 → 그 파일로 쿼리.
- **옵션 2 — 신규 영상**: 직접 촬영한 플랭크 영상을 ViTPose+정규화 파이프라인으로 추출한 JSON 으로 쿼리.

(자동화된 LOO 평가 모듈은 후속 이슈로 분리.)

### C. 에러가 났을 때
| 증상 | 원인 / 해결 |
|---|---|
| `MissingApiKeyError` | `backend/.env` 의 `GEMINI_API_KEY` 가 비어있음 |
| `UnicodeEncodeError` (cp949) | PowerShell 에서 `chcp 65001` 후 재시도 |
| ChromaDB 관련 에러 | `uv run python -m ai.rag.ingest --reset` 으로 DB 재적재 |
| Gemini 응답 느림/실패 | `--top-k 3` 으로 줄이거나, `--model gemini-2.5-flash` 로 교체 |

---

## 단계별 데이터 변환 예시

`plank_false_2.json` 을 입력으로 넣었을 때 각 단계에서 무엇이 어떻게 변하는지.

### 입력: 정규화 ViTPose JSON (발췌)

```json
{
  "model": "vitpose",
  "video_file": "plank_false_2.mp4",
  "label": "wrong",
  "normalization": {
    "steps": ["hip_center", "torso_scale", "direction_canonical"],
    "canonical_direction": "head_right",
    "coordinate_note": "hip_centered, torso_scaled (unitless, original unit: pixel)"
  },
  "total_frames": 99,
  "fps": 30.0,
  "frames": [
    {
      "frame_id": 0,
      "timestamp_ms": 0.0,
      "pose_detected": true,
      "persons": [
        {
          "norm_meta": { ... },
          "keypoints": {
            "nose":          {"x": 1.4266, "y": -0.1797, "score": 0.97, "confidence_flag": "high"},
            "left_eye":      {"x": 1.4320, "y": -0.2499, "score": 0.95, "confidence_flag": "high"},
            "right_eye":     {"x": 1.4588, "y": -0.2294, "score": 0.94, "confidence_flag": "high"},
            "left_ear":      {"x": 1.2828, "y": -0.3554, "score": 0.93, "confidence_flag": "high"},
            "right_ear":     {"x": 1.2770, "y": -0.3567, "score": 0.74, "confidence_flag": "high"},
            "left_shoulder": {"x": 0.9764, "y": -0.1961, "score": 0.95, "confidence_flag": "high"},
            "right_shoulder":{"x": 0.9701, "y": -0.2629, "score": 0.87, "confidence_flag": "high"},
            "left_elbow":    {"x": 0.5821, "y":  0.3942, "score": 0.91, "confidence_flag": "high"},
            "right_elbow":   {"x": 0.5798, "y":  0.3725, "score": 0.88, "confidence_flag": "high"},
            ... (총 17개 관절)
          }
        }
      ]
    },
    ...
  ]
}
```

좌표는 이미 hip-centered + torso-scaled 로 정규화되어 있다 → 추가 정규화 불필요.

### 1단계: `loader.iter_frames` → `FrameSample`

JSON 전체를 한 번에 메모리에 두지 않고 한 프레임씩 다음과 같은 객체로 흘려보낸다:

```python
FrameSample(
    video_file="plank_false_2.mp4",
    label="wrong",
    frame_id=0,
    timestamp_ms=0.0,
    keypoints={"nose": {"x": 1.4266, "y": -0.1797, ...}, ...},
)
```

- `pose_detected=false` 인 프레임은 자동 스킵.
- 라벨은 파일명(`plank_false_*`/`plank_true_*`)으로 판정.

### 2단계: `vectorize.frame_to_vector` → 34차원 벡터

COCO-17 관절을 정해진 순서로 (x, y) 평탄화:

```
순서: nose, left_eye, right_eye, left_ear, right_ear,
      left_shoulder, right_shoulder, left_elbow, right_elbow,
      left_wrist, right_wrist, left_hip, right_hip,
      left_knee, right_knee, left_ankle, right_ankle
```

```python
[
   1.4266, -0.1797,   #  nose
   1.4320, -0.2499,   #  left_eye
   1.4588, -0.2294,   #  right_eye
   1.2828, -0.3554,   #  left_ear
   1.2770, -0.3567,   #  right_ear
   0.9764, -0.1961,   #  left_shoulder
   0.9701, -0.2629,   #  right_shoulder
   0.5821,  0.3942,   #  left_elbow
   0.5798,  0.3725,   #  right_elbow
   ...                 # 총 34개 float
]
```

- 누락된 관절은 (0.0, 0.0) 으로 채움.
- 저신뢰 관절도 좌표 그대로 사용 — 정규화 단계에서 이미 보정됨.

### 3단계: `store` + ChromaDB → top-k 이웃

각 34차원 벡터를 ChromaDB collection `plank_frames` 에서 cosine 유사도 검색 (`top_k=5`):

```python
collection.query(query_embeddings=[vec], n_results=5, include=["metadatas", "distances"])
# 결과:
{
  "metadatas": [[
    {"label": "wrong",   "video_file": "plank_false_5.mp4", "frame_id": 12,  "timestamp_ms": 400.0},
    {"label": "wrong",   "video_file": "plank_false_1.mp4", "frame_id": 47,  "timestamp_ms": 1566.7},
    {"label": "wrong",   "video_file": "plank_false_8.mp4", "frame_id": 31,  "timestamp_ms": 1033.3},
    {"label": "correct", "video_file": "plank_true_3.mp4",  "frame_id": 102, "timestamp_ms": 3400.0},
    {"label": "wrong",   "video_file": "plank_false_4.mp4", "frame_id": 5,   "timestamp_ms": 166.7},
  ]],
  "distances": [[0.012, 0.018, 0.024, 0.041, 0.043]],
}
```

(예시 값. 실제 거리·이웃은 매번 다름.)

### 4단계: `retriever._weighted_vote` → 라벨 + confidence

가중치 `w = 1 / (distance + 1e-6)` 로 라벨별 합산:

```
wrong   : 1/0.012 + 1/0.018 + 1/0.024 + 1/0.043  ≈ 83.3 + 55.6 + 41.7 + 23.3 = 203.9
correct : 1/0.041                                 ≈ 24.4
─────────────────────────────────────────────────────────
total                                              228.3

→ label="wrong", confidence = 203.9 / 228.3 ≈ 0.893
```

각 프레임마다 다음을 만든다:

```python
FramePrediction(frame_id=0, timestamp_ms=0.0, label="wrong", confidence=0.893)
```

### 5단계: `retriever.build_timeline` → segment 압축 + 노이즈 흡수

연속된 같은 라벨 프레임을 한 segment 로 압축한 뒤, **5프레임 미만 segment 는 양옆으로 흡수**한다.

```
raw 프레임 라벨 시퀀스 (99개):
  wrong wrong wrong ... wrong correct wrong wrong ... wrong

(중간에 단발성 correct 1프레임이 끼었다면)
→ 흡수 후: 전체 99 프레임이 하나의 wrong segment
```

이번 예시(`plank_false_2.json`)의 실제 결과:

```python
RetrievalResult(
    frame_predictions=[... 99개 ...],
    timeline=[
        Segment(label="wrong", start_ms=0.0, end_ms=3266.7, frame_count=99, avg_confidence=1.00),
    ],
    total_frames=99,
    correct_ratio=0.0,
    wrong_ratio=1.0,
    video_file="plank_false_2.mp4",
    fps=30.0,
)
```

> ℹ️ `confidence=1.00` 이 비현실적으로 높은 이유는 이 입력 파일이 이미 DB 에 적재돼 있어 self-match 가 발생했기 때문. 실서비스 영상이라면 보통 0.6~0.9 사이로 떨어진다.

### 6단계: `prompt.build_prompt` → Gemini 가 받는 텍스트

#### 시스템 프롬프트 (`prompt.SYSTEM_PROMPT`)

```text
당신은 플랭크 자세를 교정해주는 한국어 운동 코치입니다.

# 평가 원칙
- 사용자 영상은 자동 검색기가 프레임 단위로 정자세(correct)/오자세(wrong) 로 분류해
  시간 구간(segment) 단위로 정리해 전달합니다.
- 당신은 그 검색 결과를 근거로만 코멘트합니다. 검색 결과에 없는 사실은 추측하지 않습니다.
- 플랭크 핵심 체크포인트(머리-목 중립, 어깨-팔꿈치 정렬, 엉덩이 처짐/들림, 몸 일직선,
  복부/둔근 활성)를 기준으로 설명합니다.
- 어조: 단정적이되 친절하게. 사용자에게 동기를 주는 한 문장을 마지막에 덧붙입니다.

# 출력 형식 (반드시 아래 마크다운 형식을 그대로 따릅니다)

## 전체 요약
(2~3문장 한국어. 잘한 비율과 주된 문제 자세 한두 가지를 짚는다.)

## 구간별 평가
- [시작초 ~ 종료초] (correct|wrong) — 한 문장 코멘트
- ...

## 핵심 개선 포인트
- (오자세가 있을 때만, 1~3개의 bullet. correct 100% 면 이 섹션을 생략)

형식을 어기면 후속 처리(UI 표시, DB 저장) 가 실패하므로 항상 위 구조를 지킵니다.
```

#### 사용자 프롬프트 (실제 출력)

```text
# 영상 메타
- 파일: plank_false_2.mp4
- fps: 30.0
- 길이: 약 3.27초
- 분석된 프레임: 99
- 정자세 비율: 0.0%
- 오자세 비율: 100.0%

# 검색기 타임라인
각 줄은 ChromaDB top-k 다수결로 결정된 자세 구간이다.
frames=구간 프레임 수, conf=거리 가중 confidence 평균.

- [  0.00s ~   3.27s] wrong (frames=99, conf=1.00)

위 타임라인만을 근거로 시스템 프롬프트의 출력 형식에 맞게 한국어 코멘트를 작성하세요.
```

### 7단계: `llm.call_gemini` → Gemini 2.5 Flash 응답 (실측)

```text
## 전체 요약
이번 플랭크 자세에서는 아쉽게도 전체 시간 동안 올바른 자세를 유지하지 못했습니다.
몸이 일직선을 이루지 못하고 주요 부위에서 자세가 무너진 것으로 보입니다.

## 구간별 평가
- [0.00s ~ 3.27s] wrong — 영상 전체 구간에서 플랭크 자세가 올바르게 유지되지 못했습니다.

## 핵심 개선 포인트
- 몸 전체가 머리부터 발뒤꿈치까지 일직선이 되도록 유지하는 데 집중해주세요. 엉덩이가
  너무 처지거나 위로 솟지 않도록 복부와 둔근을 강하게 수축하여 중립을 유지해야 합니다.
- 어깨 바로 아래 팔꿈치가 위치하도록 정렬하고, 시선은 바닥을 향해 목이 중립을 유지하도록 합니다.

꾸준히 연습하시면 분명 더 완벽한 플랭크 자세를 만드실 수 있을 거예요!
```

(약 7초 소요, Gemini 2.5 Flash 기준.)

---

## 환경변수

| 키 | 설명 |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio (https://aistudio.google.com/apikey) 에서 발급. `llm.py` 가 `.env` 에서 자동 로드. |
| `DATABASE_URL` | 본 모듈에서는 사용하지 않음 (다른 백엔드 모듈용). |

---

## 알려진 한계 & 후속 작업

- **Self-match**: 데이터셋이 적어 적재된 영상 자체를 쿼리하면 100% 매칭. LOO(leave-one-out) 평가 모듈은 별도 이슈로 분리 예정.
- **단일 운동 도메인**: 현재 플랭크만 지원. 스쿼트 등 동작이 있는 운동은 frame-level 분류로는 부족하며, 시퀀스 임베딩(혹은 동작 단위 키프레임)이 필요.
- **API 노출 미구현**: 현재는 CLI 전용. FastAPI 라우터로 `/api/v1/rag/plank/feedback` 노출은 후속 PR.
- **벡터 차원 34**: (x, y) 만 사용. score/confidence_flag 를 추가 차원으로 넣을지는 정확도 측정 후 결정.
