# ai/rag — 자세 오류 코칭 RAG

분류된 운동 자세 오류(`analysis_result`)를 입력받아, 사람이 작성한 코칭 지식 문서를
벡터 검색(RAG)하고 **Gemini Flash**로 사용자 관측값에 맞춘 코칭 코멘트를 생성한다.

---

## 1. 준비 (한 번만)

> 모든 명령은 **명령 프롬프트(cmd.exe)** 에서 `backend/` 디렉터리로 이동해 실행한다.
> 이 프로젝트의 `face-recognition`(dlib)이 Windows에서 빌드 실패하므로 `uv run` 대신
> venv의 파이썬을 직접 호출한다. 한글 깨짐 방지를 위해 `set PYTHONUTF8=1`을 먼저 실행한다.
>
> ```cmd
> cd backend
> set PYTHONUTF8=1
> ```
> `set PYTHONUTF8=1`은 그 터미널 세션 동안 유지되므로 한 번만 실행하면 된다.
> (PowerShell이라면 `$env:PYTHONUTF8=1`)

### 1-1. 의존성 설치
RAG 의존성은 이미 `.venv`에 설치돼 있다. 새 환경이라면 (한 줄로 실행):
```cmd
uv pip install langchain langchain-community langchain-text-splitters langchain-huggingface sentence-transformers langchain-chroma chromadb langchain-google-genai
```

### 1-2. API 키 설정
`backend/.env` 파일에 Gemini 키를 넣는다 ([Google AI Studio](https://aistudio.google.com/apikey)에서 발급):
```
GOOGLE_API_KEY=AIza...본인_키...
GEMINI_MODEL=gemini-2.5-flash
```

---

## 2. 실행 & 테스트 (순서대로)

### 단계 ① 인덱스 빌드
코칭 지식 문서를 임베딩해 Chroma 벡터DB에 저장한다. **최초 1회 + 문서가 바뀔 때마다** 실행.
처음 실행 시 BGE-m3 임베딩 모델(약 2GB)을 내려받는다.
```cmd
.venv\Scripts\python.exe -m ai.rag.ingest
```
기대 출력:
```
코칭 문서 인덱싱 시작 — 임베딩 모델: BAAI/bge-m3
완료: 70개 청크를 'posefit_coaching' 컬렉션에 저장
저장 위치: C:\project\posefit\backend\ai\rag\.chroma
```

### 단계 ② 검색만 테스트 (무비용, Gemini 미사용)
벡터 검색이 잘 되는지부터 확인한다. API 키가 없어도 동작한다.
```cmd
.venv\Scripts\python.exe -m ai.rag.cli ../rag_docs/group.json.txt --no-llm
```
→ 입력 오류(`골반 처짐`)에 대해 `plank_hip_sag_side_v1` 등 관련 문서가 검색되고,
그 문서들의 `코칭문구` 원문이 그대로 출력되면 검색이 정상이다.

### 단계 ③ 전체 파이프라인 (검색 + Gemini 합성)
```cmd
.venv\Scripts\python.exe -m ai.rag.cli ../rag_docs/group.json.txt
```
기대 출력 예:
```
============================================================
오류: 골반 처짐 [plank_hip_sag_side_v1] (심각도: medium)
검색된 문서: plank_false_2_w0, plank_hip_sag_side_v1, ...
------------------------------------------------------------
골반이 처지지 않도록 복부 전체를 단단하게 조여 허리를 곧게 펴고, 엉덩이 근육을
꽉 조여 몸통 라인을 수평으로 유지해 보세요. ...
주의사항: 허리 통증이 느껴지면 즉시 운동을 중단하세요.
```

### 다른 입력으로 테스트
`analysis_result.errors` 배열을 가진 JSON이면 무엇이든 입력할 수 있다.
다른 오류(예: `hip_pike`)를 가진 파일을 만들어 넣고, "검색된 문서"의 `issue_key`가
입력 오류와 일치하는지 확인하면 된다.
```cmd
.venv\Scripts\python.exe -m ai.rag.cli ../rag_docs\다른파일.json
```

### 코드에서 직접 호출
```python
from ai.rag import build_index, coach

build_index()                                  # 단계 ①
for r in coach("../rag_docs/group.json.txt"):  # 단계 ③ (--no-llm은 synthesize=False)
    print(r.error_name, "→", r.comment, r.retrieved_doc_ids)
```

---

## 3. 파이프라인 상세 — 데이터가 어떻게 바뀌는가

크게 **두 시점**이 있다.
**(A) 인덱싱 시점** — 코칭 지식 문서를 미리 벡터DB에 넣는다 (단계 ①).
**(B) 조회 시점** — 사용자 분석 결과를 받아 검색 후 코칭을 만든다 (단계 ②③).

```
(A) 인덱싱:  rag_docs/plank/*.json ──documents.py──▶ Document(본문+메타) ──BGE 임베딩──▶ Chroma(.chroma/)

(B) 조회:    group.json.txt ──query.py──▶ ErrorQuery ──to_text()──▶ 검색문장
                                 │                                      │
                                 │                          vectorstore.search (BGE+Chroma)
                                 │                                      ▼
                                 └─ 관측/기준값 ─────────────▶ 상위 k Document
                                                                        │
                                          pipeline._build_prompt ◀──────┘
                                                    │
                                              Gemini Flash
                                                    ▼
                                              코칭 코멘트
```

### (A) 인덱싱: 지식 문서 → 벡터

원본 코칭 문서 한 개 (`rag_docs/plank/plank_hip_sag_side_v1.json`, 발췌):
```json
{
  "doc_id": "plank_hip_sag_side_v1",
  "issue_key": "hip_sag",
  "라벨": "오류",
  "오류설명": "플랭크 유지 중 골반이 아래로 처지면서 ...",
  "원인가능성": ["복횡근 등 심부 코어 근육 기능 저하 ...", "..."],
  "코칭문구": ["둔근을 꽉 쥐어짜듯 조이세요. ...", "..."],
  "주의사항": "허리 통증이 느껴지면 즉시 운동을 중단하세요. ...",
  "검색키워드": ["플랭크", "골반 처짐", "측면"]
}
```

`documents.py`의 `_serialize()`가 위 JSON을 **검색 친화적 한 덩어리 텍스트(page_content)**로 직렬화한다.
(루트/v2/정상기준 등 서로 다른 스키마를 동일 의미 키로 흡수한다):
```
운동: 플랭크 / 촬영방향: 측면 / 라벨: 오류
오류: (hip_sag)
플랭크 유지 중 골반이 아래로 처지면서 ...
원인 가능성:
- 복횡근 등 심부 코어 근육 기능 저하 ...
코칭문구:
- 둔근을 꽉 쥐어짜듯 조이세요. ...
주의사항: 허리 통증이 느껴지면 ...
검색키워드: 플랭크, 골반 처짐, 측면
```
함께 **메타데이터**도 만든다 (검색 필터/원문 보존용):
```python
{"doc_id": "plank_hip_sag_side_v1", "issue_key": "hip_sag",
 "label": "오류", "view": "측면",
 "source": "plank/plank_hip_sag_side_v1.json",
 "coaching": "둔근을 꽉 쥐어짜듯 ... || 배를 안으로 당기지 말고 ..."}
```
긴 본문은 `RecursiveCharacterTextSplitter`로 800자 단위 청크 분할되고,
각 청크가 BGE-m3로 임베딩되어 `.chroma/`에 저장된다. (현재 코퍼스 = 70개 청크)

### (B) 조회: 입력 → 코칭, 한 단계씩

**0) 원본 입력** (`rag_docs/group.json.txt`):
```json
{ "analysis_result": {
    "exercise": "plank", "camera_view": "side",
    "errors": [
      { "error_code": "plank_hip_sag_side_v1", "error_name": "골반 처짐",
        "severity": "medium",
        "observed_values":  { "hip_sag_ratio_max": 0.12, "torso_line_angle_min": 164.5 },
        "threshold_values": { "hip_sag_ratio_max": 0.08, "torso_line_angle_min": 168.0 } }
    ] } }
```

**1) 파싱** — `query.parse_analysis_result()`가 `errors[]`를 `ErrorQuery`로 변환:
```python
ErrorQuery(
  error_code="plank_hip_sag_side_v1",
  error_name="골반 처짐",
  severity="medium",
  observed={"hip_sag_ratio_max": 0.12, "torso_line_angle_min": 164.5},
  threshold={"hip_sag_ratio_max": 0.08, "torso_line_angle_min": 168.0},
)
# issue_key 프로퍼티가 정규식으로 error_code에서 핵심을 추출:
#   "plank_hip_sag_side_v1" ─▶ "hip_sag"
```

**2) 검색 문장 생성** — `ErrorQuery.to_text()`:
```
플랭크 측면 자세 오류: 골반 처짐(hip_sag). hip_sag_ratio_max 관측 0.12 (기준 0.08). torso_line_angle_min 관측 164.5 (기준 168.0).
```

**3) 벡터 검색** — `vectorstore.search()`.
먼저 메타데이터 필터 `where={"issue_key": "hip_sag"}`로 같은 오류 유형의 문서만 좁힌 뒤,
부족하면 전체에서 의미 유사도로 보강한다. 결과(상위 k=4):
```
검색된 문서: plank_false_2_w0, plank_hip_sag_side_v1, plank_hip_sag_side_v1, plank_false_2_w0
```
> `error_code`(plank_hip_sag_side_v1)가 지식 문서의 `doc_id`와 그대로 일치해, 정답 문서가 최상위에 잡힌다.

**4) 프롬프트 조립** — `pipeline._build_prompt()`가 *입력 관측값 + 검색된 지식*을 합친다:
```
## 감지된 오류
골반 처짐 (hip_sag), 심각도: medium

## 관측값
- hip_sag_ratio_max: 관측 0.12 (기준 0.08)
- torso_line_angle_min: 관측 164.5 (기준 168.0)

## 참고 코칭 지식
[문서 plank_hip_sag_side_v1 | issue=hip_sag | label=오류]
운동: 플랭크 / 촬영방향: 측면 / 라벨: 오류
... (3-A에서 만든 page_content) ...

위 오류에 대한 코칭 코멘트를 작성하세요.
```
시스템 프롬프트는 "참고 지식에 없는 사실은 지어내지 말 것"을 지시해 환각을 억제한다.

**5) Gemini Flash 합성** — 최종 코칭 코멘트 (`Coaching.comment`):
```
골반이 처지지 않도록 복부 전체를 단단하게 조여 허리를 곧게 펴고, 엉덩이 근육을 꽉
조여 몸통 라인을 수평으로 유지해 보세요. 마치 배에 주먹을 맞을 것처럼 복부에 힘을
주고, 발뒤꿈치로 뒤쪽 벽을 밀어내는 느낌을 가지면 자세 유지에 도움이 됩니다.
주의사항: 허리 통증이 느껴지면 즉시 운동을 중단하세요.
```
`errors`가 여러 개면 위 1~5를 오류마다 반복해 `Coaching` 리스트를 반환한다.

---

## 4. 구성 요소

| 파일 | 역할 |
|------|------|
| `config.py` | 경로·모델명·검색 파라미터 (env로 덮어쓰기) |
| `documents.py` | 코칭 JSON(루트/v2/정상기준 스키마) → LangChain `Document` |
| `vectorstore.py` | BGE-m3 임베딩 + Chroma 인덱스 빌드/검색 |
| `query.py` | `analysis_result.errors` → `ErrorQuery` 파싱 |
| `pipeline.py` | 검색 + Gemini 합성 (`coach()`) |
| `ingest.py` / `cli.py` | 인덱스 빌드 / 코칭 조회 CLI |

### 설정 (`config.py`, 모두 env로 덮어쓰기 가능)
- `GOOGLE_API_KEY` — Gemini 키 (합성에 필요)
- `GEMINI_MODEL` — 생성 모델 (기본 `gemini-2.5-flash`)
- `BGE_MODEL` — 임베딩 모델 (기본 `BAAI/bge-m3`)
- `TOP_K` — 오류당 검색 문서 수 (기본 4)
- `source_globs` — 지식 베이스 범위. 기본은 `plank/*.json`(오류별 사례),
  `plank/v2/*.json`(window별 사례), `plank/v2/correct/*.json`·`exam.json`(정상 기준).
  원천 feature(`windows/`)와 중복본(`v2 copy/`)은 제외.

### LLM 교체
Gemini → Claude 등은 `pipeline.py`의 `_get_llm()` 한 곳만 바꾸면 된다.
