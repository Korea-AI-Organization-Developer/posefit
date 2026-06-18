# Plank Side Error RAG Korean Corpus

이 패키지는 측면 플랭크 자세 분석에서 감지되는 7가지 오류에 대해 한국어 코칭용 RAG 문서를 확장한 코퍼스입니다.

## 포함 파일

- `plank_rag_korean_corpus/`: 개별 JSON 파일 98개
- `plank_rag_korean_corpus_array.json`: 전체 JSON 배열
- `plank_rag_chroma_documents.jsonl`: ChromaDB 임베딩용 JSONL
- `plank_rag_manifest.json`: 코퍼스 메타데이터
- `plank_rag_korean_json_files.zip`: 개별 JSON 파일 ZIP

## 생성 범위

오류코드별 14개 문서씩, 총 98개 문서입니다.

오류코드:

- `plank_ankle_misalignment_side_v1`: 14 docs
- `plank_elbow_deviation_side_v1`: 14 docs
- `plank_head_drop_side_v1`: 14 docs
- `plank_head_rise_side_v1`: 14 docs
- `plank_hip_pike_side_v1`: 14 docs
- `plank_hip_sag_side_v1`: 14 docs
- `plank_shoulder_collapse_side_v1`: 14 docs

## ChromaDB 권장 적재 방식

JSON 전체를 그대로 임베딩해도 되지만, 검색 품질을 위해 `plank_rag_chroma_documents.jsonl`의 `document` 필드를 임베딩하고 `metadata`를 함께 저장하는 방식을 권장합니다.

```python
import json
import chromadb

client = chromadb.PersistentClient(path="./chroma")
collection = client.get_or_create_collection("plank_form_rag_ko")

ids, documents, metadatas = [], [], []
with open("plank_rag_chroma_documents.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        ids.append(row["id"])
        documents.append(row["document"])
        metadatas.append(row["metadata"])

collection.add(ids=ids, documents=documents, metadatas=metadatas)
```

## 검색 팁

1. 분석 결과에 `error_code`가 있으면 `metadata.error_code` 필터를 먼저 사용하세요.
2. 필터 없이 전체 검색할 때는 입력 JSON에서 `exercise`, `camera_view`, `error_code`, `error_name`, `observed_values`, `threshold_values`, `time_range`를 자연어로 풀어 query에 포함하면 좋습니다.
3. LLM에 넘길 때는 상위 3~5개 문서를 합치되, 같은 오류의 서로 다른 관점 문서가 섞이도록 MMR 또는 diversity search를 사용하면 답변이 덜 반복됩니다.
4. 최종 코멘트는 “문제 설명 → 원인/위험 → 즉시 교정 큐 → 다음 세트 조절 → 통증 시 중단” 순서가 가장 안정적입니다.

## 안전 문구

이 문서는 운동 자세 코칭 보조용입니다. 통증, 저림, 날카로운 불편감이 있으면 운동을 중단하고 전문가의 평가를 받으세요.
