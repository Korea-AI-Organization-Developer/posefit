# backend/ai — AI·비전 모듈 안내

운동 자세 분석에 사용되는 AI/비전 관련 코드를 모아 놓은 패키지입니다.

```
backend/ai/
├ face/              # 얼굴 인식 모듈
├ pose/              # 포즈 추정 모듈 (ViTPose-Base)
└ llm/               # LangGraph 기반 운동 피드백 생성 모듈
```

---

## 폴더별 설명

### `face/`
얼굴 인식 기능을 담당합니다.

- `face_recognizer.py` — 얼굴 감지·인식 로직

---

### `pose/`
웹캠 영상에서 관절 키포인트를 추출하는 포즈 추정 모듈입니다 (ViTPose-Base 사용).

---

### `llm/`
LangGraph를 사용해 포즈 분석 결과를 바탕으로 운동 피드백을 생성하는 모듈입니다.

#### 파일 구성

| 파일 | 설명 |
|---|---|
| `langgraph_V1.py` | LangGraph 그래프 정의 및 노드 구현 |
| `input_exam.json` | 그래프 입력 예시 데이터 (`analysis_result` 구조) |
| `posefit_graph.png` | 컴파일된 그래프 구조 시각화 이미지 |
| `langgraph_demo.jpg` | 데모 스크린샷 |

#### 그래프 구조 (`langgraph_V1.py`)

LLM은 **Google Gemini** (`langchain_google_genai`)를 사용하며, 환경변수 `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`가 필요합니다.

피드백 유형에 따라 세 가지 경로로 분기됩니다.

```
START
  └─▶ branch_node ──────────────────────────────────┐
        │                                            │
        ├─ set (단일 세트) ──▶ norm2feature          │
        │                        └─▶ feature2seg     │
        │                              └─▶ pose_decide_node
        │                                    └─▶ coaching_generator_node (RAG+LLM)
        │                                          └─▶ set_text_summarize_node
        │                                                └─▶ set_review_node ──▶ END
        │
        ├─ daily (일일 종합) ──▶ daily_feedback_node
        │                           └─▶ daily_text_summarize_node
        │                                 └─▶ daily_review_node ──▶ END
        │
        └─ long_term (장기 종합) ──▶ long_term_feedback_node
                                        └─▶ long_text_summarize_node
                                              └─▶ long_review_node ──▶ END
```

#### 입력에 따른 분기 조건

| 조건 | 경로 | 설명 |
|---|---|---|
| `historical_analysis_results` 있음 | `long_term` | 해당 운동의 전체 기록 기반 장기 피드백 |
| `today_set_results` 있음 | `daily` | 오늘 수행한 전체 세트 종합 피드백 |
| 그 외 | `set` | 단일 세트 실시간 피드백 |

#### `FeedbackState` 주요 필드

| 필드 | 노드 | 설명 |
|---|---|---|
| `normalized_pose` | 입력 | 영상에서 추출한 정규화된 포즈 JSON |
| `frame_features` | `norm2feature` 출력 | 프레임별 각도·비율·신뢰도 |
| `segment_features` | `feature2seg` 출력 | 윈도우 단위로 묶은 feature |
| `analysis_result` | `pose_decide_node` 출력 | 오류명·수준·부위·발생 구간 |
| `retrieved_docs` | `coaching_generator_node` 출력 | RAG 검색 결과 |
| `set_feedback` | `coaching_generator_node` 출력 | 세트 피드백 원문 |
| `feedback_text` | `*_text_summarize_node` 출력 | 정리된 텍스트 피드백 |
| `final_feedback` | `*_review_node` 출력 | 화면 출력용 최종 피드백 |

#### 환경변수

```
GOOGLE_API_KEY=...   # 또는 GEMINI_API_KEY
GEMINI_MODEL=...     # 기본값: gemini-3.1-flash-lite
```

#### 그래프 이미지 재생성

```bash
cd backend
uv run python -c "from ai.llm.langgraph_V1 import save_graph_image; save_graph_image()"
```
