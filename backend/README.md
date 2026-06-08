# PoseFit Backend 구조 안내

FastAPI 초심자를 위한 백엔드 폴더 구조와 계층(layer) 설명서.
실행 방법은 [루트 README](../README.md)를 참고하세요.

---

## 폴더 구조

```
backend/app/
├ main.py          # FastAPI 앱 진입점 (앱 생성, 미들웨어, 라우터 등록)
├ config.py        # 환경변수 설정 (.env 읽기)
├ database.py      # DB 연결 (engine / Base / get_db)
│
├ models/          # ① DB 테이블 정의 (SQLAlchemy ORM)
├ schemas/         # ② 요청/응답 데이터 형식 (Pydantic)
├ repositories/    # ③ DB 접근 (SELECT/INSERT 같은 쿼리)
├ services/        # ④ 비즈니스 로직 (실제 처리 + 트랜잭션)
└ routers/         # ⑤ API 엔드포인트 (URL ↔ 함수 연결)
```

> 현재 `schemas/` `repositories/` `services/` `routers/` 는 **빈 패키지**입니다.
> 기능을 맡은 사람이 그 폴더에 파일을 추가하면 됩니다.
> `models/` 만 `docs/erd.sql` 기준으로 미리 채워져 있습니다.

---

## 각 계층이 하는 일

요청 하나가 들어오면 아래 순서로 흘러갑니다. **식당**에 비유하면 이해하기 쉽습니다.

| 계층 | 역할 | 식당 비유 |
|---|---|---|
| **routers/** | URL과 HTTP 메서드를 함수에 연결. 입력을 받아 service 호출 | 주문을 받는 **점원** |
| **schemas/** | 들어오는/나가는 데이터의 형식·유효성 검사 (Pydantic) | 주문서 **양식** |
| **services/** | 실제 처리 로직. "무엇을 할지" 결정하고 DB 저장(commit) | 요리하는 **주방장** |
| **repositories/** | DB에 직접 질의 (조회/저장/삭제) | 재료를 꺼내오는 **창고지기** |
| **models/** | DB 테이블의 파이썬 표현 (컬럼·관계) | 창고 속 **재료(데이터)** |
| **database.py** | DB 연결과 세션 관리 | 창고로 가는 **통로** |

### 요청 흐름

```
HTTP 요청
   │
   ▼
routers/   ──(schemas로 입력 검증)──▶  요청 데이터
   │
   ▼
services/  ── 비즈니스 로직, commit
   │
   ▼
repositories/ ── DB 쿼리
   │
   ▼
models/ ↔ database.py ↔  MySQL
   │
   ▼
services → routers ──(schemas로 응답 직렬화)──▶  HTTP 응답
```

핵심 규칙:
- **routers 는 얇게**: 입력 받고 service 호출만. 로직을 넣지 않는다.
- **services 가 로직의 중심**: 여러 repository를 조합하고, 트랜잭션(`commit`)을 책임진다.
- **repositories 는 쿼리만**: `commit` 하지 않고 조회/추가까지만.
- **models 와 schemas 는 다르다**: models = DB 테이블, schemas = API 입출력 형식.

---

## 새 기능 추가하는 순서 (예시: "운동 종목 목록 조회 API")

아래 순서대로 파일을 만들면 됩니다. (파일명은 도메인 이름으로)

1. **models/** — 테이블이 이미 있으면 그대로 사용 (`models/exercise.py`)
2. **schemas/exercise.py** — 응답 형식 정의
   ```python
   from pydantic import BaseModel, ConfigDict

   class ExerciseRead(BaseModel):
       model_config = ConfigDict(from_attributes=True)  # ORM 객체 → 응답 변환
       id: int
       name_ko: str
   ```
3. **repositories/exercise.py** — DB 조회
   ```python
   from sqlalchemy import select
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.models.exercise import Exercise

   class ExerciseRepository:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def list(self):
           result = await self.db.execute(select(Exercise))
           return result.scalars().all()
   ```
4. **services/exercise.py** — 로직
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.repositories.exercise import ExerciseRepository

   class ExerciseService:
       def __init__(self, db: AsyncSession):
           self.repo = ExerciseRepository(db)

       async def list(self):
           return await self.repo.list()
   ```
5. **routers/exercise.py** — 엔드포인트
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.database import get_db
   from app.schemas.exercise import ExerciseRead
   from app.services.exercise import ExerciseService

   router = APIRouter(prefix="/exercises", tags=["exercises"])

   @router.get("", response_model=list[ExerciseRead])
   async def list_exercises(db: AsyncSession = Depends(get_db)):
       return await ExerciseService(db).list()
   ```
6. **main.py** — 라우터 등록
   ```python
   from app.routers import exercise
   app.include_router(exercise.router, prefix="/api")
   ```

→ 서버 실행 후 `http://localhost:8000/docs` 에서 바로 테스트할 수 있습니다.

---

## 자주 쓰는 개념

- **`Depends(get_db)`**: 요청마다 DB 세션을 자동으로 만들어 주입(의존성 주입)하는 FastAPI 기능.
- **`async` / `await`**: DB가 응답하는 동안 다른 요청을 처리하기 위한 비동기 문법. router·service·repository 함수는 `async def` 로 작성.
- **commit**: DB에 변경을 확정 저장. 본 프로젝트에서는 **service 계층에서만** 호출한다.
- **ORM**: 파이썬 객체 ↔ DB 테이블을 자동 매핑 (SQLAlchemy). SQL을 직접 안 써도 됨.

---

## 참고

- DB 스키마(테이블 정의): [docs/erd.sql](../docs/erd.sql)
- 요구사항: [docs/requirements.md](../docs/requirements.md)
- 실행 방법·환경설정: [루트 README](../README.md)
- FastAPI 공식 튜토리얼: https://fastapi.tiangolo.com/ko/tutorial/
