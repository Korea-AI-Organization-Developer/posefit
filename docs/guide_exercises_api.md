# 운동 목록 API 만들기 — 처음부터 끝까지

> **이 문서는 무엇인가요?**
> PoseFit 프로젝트에서 "운동 종목 목록" API(`GET /api/v1/exercises`) 하나를 처음부터 끝까지 구현하는 전 과정을 기록한 학습 자료입니다. 백엔드·프론트엔드·Next.js·FastAPI를 거의 모르는 팀원도 따라올 수 있도록, 모든 용어와 개념을 그때그때 풀어서 설명합니다.
>
> 화면(`/workout`)에 운동 카드 4개가 뜨기까지, **명세서를 읽는 것부터 → 백엔드 코드 → 데이터베이스 → 프론트엔드 코드 → 브라우저 확인**까지의 한 흐름을 다룹니다.

---

## 0. 이 문서를 다 읽으면 알게 되는 것

- 웹 서비스에서 "프론트엔드", "백엔드", "API", "데이터베이스"가 각각 무슨 일을 하고 어떻게 대화하는지
- API 명세서(`openapi.yaml`)를 읽고, 거기 적힌 대로 백엔드 엔드포인트를 만드는 방법
- FastAPI 백엔드의 "레이어드 구조"(routers → services → repositories → models)가 왜 그렇게 나뉘어 있는지
- Next.js 프론트엔드가 백엔드 API를 불러와 화면에 그리는 방법
- "가짜 데이터(mock)"로 먼저 화면을 만들고, 나중에 진짜 API로 갈아끼우는 실무 전략

---

## 1. 큰 그림 — 우리가 만드는 것은 무엇인가

사용자가 웹 브라우저에서 `localhost:3000/workout` 페이지에 들어가면, **운동 카드 목록**(런지·플랭크·푸쉬업·오버헤드프레스)이 보여야 합니다. 이 카드에 들어갈 데이터는 어디서 올까요? **데이터베이스**에 저장돼 있고, **백엔드**가 그걸 꺼내서 **API**로 내보내고, **프론트엔드**가 그걸 받아 **화면**에 그립니다.

이 4단계를 한 줄로 그리면 이렇습니다.

```
[데이터베이스]  →  [백엔드(FastAPI)]  →  [API: GET /api/v1/exercises]  →  [프론트엔드(Next.js)]  →  [브라우저 화면]
  운동 데이터        데이터를 꺼내            JSON으로 응답                   받아서 카드로 그림        사용자가 봄
  저장돼 있음         가공함
```

우리가 이번에 만드는 것은 가운데의 **백엔드 + API** 부분과, 오른쪽의 **프론트엔드가 그 API를 호출하도록 연결**하는 부분입니다.

### 핵심 용어 4개 (여기서 먼저 짚고 갑니다)

- **프론트엔드(Frontend)**: 사용자가 눈으로 보고 클릭하는 화면. 우리 프로젝트는 **Next.js**(리액트 기반 도구)로 만듭니다. 브라우저에서 돕니다.
- **백엔드(Backend)**: 화면 뒤에서 데이터를 처리하는 서버. 우리 프로젝트는 **FastAPI**(파이썬 도구)로 만듭니다. 사용자 눈에는 안 보입니다.
- **API**: 프론트엔드와 백엔드가 대화하는 "약속된 창구". 예) "운동 목록 줘"라고 프론트가 `GET /api/v1/exercises` 주소로 요청하면, 백엔드가 운동 목록을 돌려줍니다.
- **데이터베이스(DB)**: 데이터를 영구히 저장하는 창고. 우리 프로젝트는 **MySQL**을 씁니다.

---

## 2. 사전 지식 — 웹은 어떻게 대화하나

코드를 보기 전에, API가 오가는 방식을 아주 기초부터 설명합니다.

### 2-1. 클라이언트와 서버

웹은 **요청하는 쪽(클라이언트)**과 **응답하는 쪽(서버)**의 대화입니다. 식당에 비유하면, 손님(클라이언트)이 "스테이크 주세요"라고 주문하면 주방(서버)이 음식을 만들어 내옵니다. 우리 경우 **브라우저/프론트엔드가 클라이언트**, **FastAPI 백엔드가 서버**입니다.

### 2-2. HTTP 요청은 "동사 + 주소"로 이뤄진다

요청에는 **무엇을 할지(메서드)**와 **어디에(경로)**가 들어갑니다.

| 메서드 | 의미 | 일상 비유 |
|---|---|---|
| **GET** | 데이터를 **조회**한다 (가져오기) | "메뉴판 보여줘" |
| **POST** | 데이터를 **새로 만든다** | "주문 넣을게" |
| **PUT/PATCH** | 데이터를 **수정**한다 | "주문 바꿀게" |
| **DELETE** | 데이터를 **삭제**한다 | "주문 취소" |

우리가 만드는 운동 목록은 "가져오기"이므로 **GET**입니다. 주소(경로)는 `/api/v1/exercises`입니다.

- `/api` = API라는 네임스페이스(이 주소들은 API용이라는 표시)
- `/v1` = API 버전 1 (나중에 크게 바뀌면 `/v2`를 따로 둘 수 있음)
- `/exercises` = "운동들"이라는 자원(resource) 이름

### 2-3. 응답은 JSON으로 온다

서버는 데이터를 **JSON**이라는 글자 형식으로 돌려줍니다. JSON은 사람도 읽을 수 있는 "이름: 값" 묶음입니다.

```json
{
  "items": [
    { "id": 1, "nameKo": "런지", "nameEn": "Lunge", "exerciseType": "dynamic", "isActive": true, "userAvgScore": null }
  ]
}
```

- `{ }` 는 객체(묶음), `[ ]` 는 배열(목록)
- `"nameKo": "런지"` 는 "nameKo라는 이름표에 런지라는 값"
- 프론트엔드는 이 JSON을 받아서 `nameKo`를 카드 제목에, `exerciseType`을 "동적/정적" 라벨에 꽂아 넣습니다.

> **왜 camelCase(`nameKo`)인가?** 파이썬(백엔드)은 보통 `name_ko`처럼 밑줄(snake_case)을 쓰고, 자바스크립트(프론트엔드)는 `nameKo`처럼 낙타등(camelCase)을 씁니다. 우리는 **API로 주고받을 때는 camelCase로 통일**하기로 약속했습니다. (이 변환을 백엔드가 자동으로 해줍니다 — 뒤에서 설명)

---

## 3. 프로젝트 구조 — 모노레포

PoseFit은 **모노레포(monorepo)**입니다. 프론트엔드·백엔드·문서가 하나의 깃 저장소 안에 폴더로 나뉘어 함께 있습니다.

```
posefit/
├ backend/      ← 백엔드 (FastAPI, 파이썬). 패키지 관리는 uv
├ frontend/     ← 프론트엔드 (Next.js, 타입스크립트). 패키지 관리는 npm
├ docs/         ← 문서 (이 파일, API 명세서 openapi.yaml, ERD 등)
└ docker-compose.yaml  ← 개발용 MySQL 데이터베이스를 띄우는 설정
```

이번 작업은 `backend/`에 코드를 추가하고, `frontend/`의 일부를 수정하고, `docs/`의 명세서를 따릅니다.

---

## 4. 출발점 — API 명세서(`openapi.yaml`) 읽기

코드를 짜기 전, **"무엇을 만들지"는 이미 `docs/openapi.yaml`에 정해져 있습니다.** 이 파일이 팀의 약속(계약서)입니다. 백엔드는 이 약속대로 응답을 만들고, 프론트엔드는 이 약속대로 데이터가 올 거라 믿고 화면을 짭니다. 그래서 **명세서를 먼저 읽는 것이 출발점**입니다.

`/exercises` 부분을 발췌하면 다음과 같습니다.

```yaml
/exercises:
  get:
    operationId: listExercises
    summary: 운동 종목 목록 — SCR-06
    parameters:
      - name: activeOnly
        in: query
        schema: { type: boolean, default: true }   # ?activeOnly=true 같은 쿼리 파라미터
    responses:
      '200':                                        # 성공 시
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ExerciseListResponse'   # 이런 모양으로 응답해라
```

이 명세가 말하는 것을 한국어로 풀면:

- **GET `/exercises`** 주소로 요청을 받는다.
- **`activeOnly`**라는 선택 옵션을 쿼리(주소 뒤 `?activeOnly=true`)로 받을 수 있다. 기본값은 `true`(노출 중인 운동만).
- 성공하면 **`ExerciseListResponse` 모양의 JSON**으로 응답한다.

그리고 응답의 모양(`ExerciseListResponse`)은 명세서 아래쪽에 이렇게 정의돼 있습니다.

```yaml
ExerciseSummary:                 # 운동 한 개의 요약 정보
  properties:
    id:            { type: integer }
    nameKo:        { type: string }                  # 한글 이름
    nameEn:        { type: ["string", "null"] }      # 영문 이름 (없으면 null)
    exerciseType:  { enum: [static, dynamic] }       # 정적/동적
    isActive:      { type: boolean }                 # 노출 여부
    userAvgScore:  { type: ["number", "null"] }      # 이 사용자의 평균 점수 (안 했으면 null)

ExerciseListResponse:            # 목록 응답
  properties:
    items: [ ExerciseSummary, ... ]                  # 운동 요약들의 배열
```

> **`userAvgScore`가 핵심 포인트입니다.** 이 값은 "운동 테이블"에 그냥 저장돼 있는 게 아니라, **이 API를 호출한 사용자가 그 운동을 했던 기록들의 평균**입니다(명세서 표현으로 "Derived", 즉 계산해서 만들어내는 값). 그래서 단순 조회가 아니라 **두 테이블을 합치는(JOIN) 계산**이 필요합니다. 뒤에서 다룹니다.

---

## 5. 백엔드 구현 (FastAPI) — 레이어드 구조

### 5-1. 왜 파일을 여러 개로 나누나? (레이어드 아키텍처)

초보자는 보통 "코드 한 파일에 다 넣으면 안 되나?"라고 생각합니다. 작동은 하지만, 프로젝트가 커지면 뒤죽박죽이 됩니다. 그래서 우리는 **역할별로 층(layer)을 나눕니다.** 식당에 비유하면 이렇습니다.

| 층(폴더) | 하는 일 | 식당 비유 |
|---|---|---|
| **routers/** | URL과 함수를 연결, 입력 받아 service 호출 | 주문받는 **점원** |
| **schemas/** | 들어오고 나가는 데이터의 형식·검증 | 주문서 **양식** |
| **services/** | 실제 처리 로직, 트랜잭션 저장(commit) | 요리하는 **주방장** |
| **repositories/** | 데이터베이스에 직접 질의(조회/저장) | 창고에서 재료 꺼내는 **창고지기** |
| **models/** | 데이터베이스 테이블의 파이썬 표현 | 창고 속 **재료** |

**규칙 (이게 프로젝트의 약속입니다):**
- **routers는 얇게** — 입력만 받아 service를 부르고, 비즈니스 로직은 넣지 않는다.
- **로직과 저장(commit)은 services에서만** — repositories는 조회/추가까지만 한다.
- **models ≠ schemas** — models는 DB 테이블, schemas는 API 입출력. 둘은 다른 것이다.

요청 하나가 흐르는 순서:

```
HTTP 요청
   │
   ▼
routers/      ← 입력을 받는다 (URL, 쿼리 파라미터)
   │
   ▼
services/     ← "무엇을 할지" 결정한다 (로직)
   │
   ▼
repositories/ ← 데이터베이스에 질의한다 (SELECT)
   │
   ▼
models/ ↔ MySQL  ← 실제 데이터
   │
   ▼
다시 위로 올라가며 schemas/ 로 JSON 응답을 만든다
```

### 5-2. 디렉토리 — 무엇을 새로 만드나

운동 목록 API를 위해 `backend/app/` 아래 **파일 4개를 새로 만들고, 1개를 수정**합니다.

```
backend/app/
├ main.py                    ← (수정) 라우터 등록 한 줄 추가
├ models/
│   └ exercise.py            ← (이미 있음) DB 테이블 정의. 손대지 않음
├ schemas/
│   └ exercise.py            ← (신규) API 응답 형식
├ repositories/
│   └ exercise.py            ← (신규) DB 조회 + 평균점수 JOIN
├ services/
│   └ exercise.py            ← (신규) 로직 (얇음)
└ routers/
    └ exercise.py            ← (신규) GET /exercises 엔드포인트
```

이제 **데이터가 흐르는 역순**(가장 안쪽 models부터)으로 하나씩 만들어 봅니다. 그래야 각 층이 무엇에 기대고 있는지 이해하며 쌓을 수 있습니다.

### 5-3. ① models — DB 테이블 (이미 존재)

`models`는 데이터베이스의 `exercises` 테이블을 파이썬 클래스로 표현한 것입니다. 이미 만들어져 있어 **손대지 않습니다.** 어떻게 생겼는지만 봅니다.

```python
# backend/app/models/exercise.py
class Exercise(Base):
    __tablename__ = "exercises"          # 실제 DB 테이블 이름

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name_ko: Mapped[str] = mapped_column(String(100), nullable=False)          # 한글 이름
    name_en: Mapped[str | None] = mapped_column(String(100), nullable=True)    # 영문 이름 (없을 수 있음)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    exercise_type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType), ...)  # static | dynamic
    is_active: Mapped[bool] = mapped_column(Boolean, ...)                          # 노출 여부
```

- `Mapped[int]`, `Mapped[str | None]` 은 "이 컬럼은 정수다 / 글자인데 없을 수도 있다(`None`)"라는 타입 표시입니다.
- 이 클래스 하나가 DB 테이블 한 개와 1:1로 연결됩니다. 이런 도구를 **ORM**(객체-관계 매핑)이라 부릅니다. 덕분에 SQL을 직접 안 쓰고 파이썬 객체로 DB를 다룰 수 있습니다.

평균 점수 계산에 필요한 또 다른 테이블도 봅니다 — **운동 일별 통계** 테이블입니다.

```python
# backend/app/models/workout.py 일부
class WorkoutDailyStat(Base):
    __tablename__ = "workout_daily_stats"
    user_id: ...        # 누구의
    exercise_id: ...    # 어떤 운동의
    stat_date: ...      # 며칠의 통계인지
    avg_score: Mapped[Decimal | None]   # 그날 그 운동의 평균 점수
```

→ 사용자의 운동 평균 점수(`userAvgScore`)는 이 `workout_daily_stats` 테이블의 `avg_score`를 사용자·운동별로 평균 내서 구합니다.

### 5-4. ② schemas — API 응답 형식

`schemas`는 **API로 나가는 데이터의 모양**을 정의합니다. 명세서의 `ExerciseSummary`/`ExerciseListResponse`를 그대로 파이썬으로 옮긴 것입니다. 도구는 **Pydantic**을 씁니다.

```python
# backend/app/schemas/exercise.py
from decimal import Decimal
from app.models.enums import ExerciseType
from app.schemas.base import CamelModel


class ExerciseSummary(CamelModel):       # 운동 한 개의 요약
    id: int
    name_ko: str
    name_en: str | None                  # None = "없을 수 있음" (명세의 nullable)
    exercise_type: ExerciseType          # static | dynamic 둘 중 하나만 허용
    is_active: bool
    user_avg_score: Decimal | None       # 안 한 운동이면 None


class ExerciseListResponse(CamelModel):  # 목록 응답
    items: list[ExerciseSummary]         # 요약들의 리스트
```

여기서 `CamelModel`을 상속하는 게 중요합니다. 이건 우리가 만든 공통 베이스인데, **파이썬 안에서는 `name_ko`(snake_case)로 쓰되, JSON으로 내보낼 때 자동으로 `nameKo`(camelCase)로 바꿔주는** 설정이 들어 있습니다.

```python
# backend/app/schemas/base.py
class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,    # 출력 시 name_ko → nameKo 자동 변환
        populate_by_name=True,
        from_attributes=True,        # ORM 객체(models)에서 바로 값을 읽어올 수 있게
    )
```

> **왜 schemas와 models를 따로 두나?** models는 "DB에 어떻게 저장되는가", schemas는 "API로 어떻게 보이는가"입니다. 예를 들어 `userAvgScore`는 DB 테이블(`exercises`)에는 없는 계산값이라 schema에만 있습니다. 둘을 분리해야 DB 구조와 API 모양을 독립적으로 바꿀 수 있습니다.

### 5-5. ③ repositories — DB 조회 (여기서 JOIN)

`repositories`는 **데이터베이스에 실제로 질의**하는 층입니다. 이번 API의 가장 어려운 부분, 즉 **운동 목록을 가져오면서 동시에 그 사용자의 평균 점수를 계산**하는 일이 여기서 일어납니다.

```python
# backend/app/repositories/exercise.py
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exercise import Exercise
from app.models.workout import WorkoutDailyStat


class ExerciseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db                       # DB 세션(연결)을 받아 보관

    async def list(self, user_id: int, active_only: bool = True):
        # ① 이 사용자의 "운동별 평균 점수"를 미리 계산하는 작은 조회(서브쿼리)
        avg_subq = (
            select(
                WorkoutDailyStat.exercise_id,
                func.avg(WorkoutDailyStat.avg_score).label("user_avg_score"),
            )
            .where(WorkoutDailyStat.user_id == user_id)   # 이 사용자 기록만
            .group_by(WorkoutDailyStat.exercise_id)        # 운동별로 묶어서
            .subquery()
        )

        # ② 운동 목록에 위 평균을 "이어 붙인다"(LEFT JOIN)
        stmt = select(Exercise, avg_subq.c.user_avg_score).outerjoin(
            avg_subq, Exercise.id == avg_subq.c.exercise_id
        )
        if active_only:
            stmt = stmt.where(Exercise.is_active.is_(True))   # 노출 운동만

        result = await self.db.execute(stmt)
        return result.all()                # (운동, 평균점수) 쌍들의 목록
```

조금 어렵게 느껴지는 3가지 개념을 풀어 설명합니다.

- **서브쿼리(subquery)**: "큰 조회 안에 들어가는 작은 조회"입니다. 먼저 사용자의 운동별 평균 점수표를 만들어 둡니다.
- **JOIN(조인)**: 두 테이블을 연결해 한 줄로 합치는 것입니다. "운동 테이블"과 "방금 만든 평균 점수표"를 `exercise_id`가 같은 것끼리 잇습니다.
- **LEFT JOIN(outerjoin)**: 왜 일반 JOIN이 아니라 LEFT JOIN일까요? **한 번도 안 한 운동**은 평균 점수표에 없습니다. 일반 JOIN이면 그런 운동이 목록에서 통째로 빠져버립니다. LEFT JOIN은 "운동은 무조건 다 보여주되, 평균이 없으면 그 자리에 빈 값(`null`)을 넣어라"는 뜻입니다. 그래서 안 해본 운동도 목록에 나오고 `userAvgScore`만 `null`이 됩니다.

> **규칙 복습**: repository는 조회만 합니다. `commit`(저장 확정)은 하지 않습니다. 이번 API는 읽기만 하므로 commit 자체가 없지만, 데이터를 바꾸는 API라면 commit은 다음 층(services)에서 합니다.

### 5-6. ④ services — 로직 (이번엔 얇음)

`services`는 "무엇을 할지" 결정하는 로직의 중심입니다. 이번 API는 로직이 단순(그냥 조회 결과를 응답 모양으로 정리)해서 얇습니다.

```python
# backend/app/services/exercise.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.exercise import ExerciseRepository
from app.schemas.exercise import ExerciseListResponse, ExerciseSummary


class ExerciseService:
    def __init__(self, db: AsyncSession):
        self.repo = ExerciseRepository(db)        # repository를 품고 있음

    async def list(self, user: User, active_only: bool = True) -> ExerciseListResponse:
        rows = await self.repo.list(user.id, active_only)   # DB에서 (운동, 평균) 목록을 받아
        items = [
            ExerciseSummary(                                # 응답 형식(schema)으로 변환
                id=exercise.id,
                name_ko=exercise.name_ko,
                name_en=exercise.name_en,
                exercise_type=exercise.exercise_type,
                is_active=exercise.is_active,
                user_avg_score=user_avg_score,
            )
            for exercise, user_avg_score in rows            # 각 쌍을 하나씩 꺼내서
        ]
        return ExerciseListResponse(items=items)            # 최종 응답 객체
```

- repository가 돌려준 `(운동, 평균점수)` 쌍들을 하나씩 꺼내(`for exercise, user_avg_score in rows`), 명세서 모양의 `ExerciseSummary`로 바꿔 리스트에 담습니다.
- 이렇게 만든 `ExerciseListResponse`가 그대로 API 응답이 됩니다(camelCase 변환은 schema가 자동으로).

### 5-7. ⑤ routers — 엔드포인트 (URL 연결)

`routers`는 **URL과 함수를 연결**하는 가장 바깥 층입니다. 명세서의 `GET /exercises`, 쿼리 파라미터 `activeOnly`가 여기서 코드가 됩니다.

```python
# backend/app/routers/exercise.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.exercise import ExerciseListResponse
from app.services.exercise import ExerciseService

router = APIRouter(prefix="/exercises", tags=["Exercises"])   # 이 파일의 주소들은 /exercises 로 시작


@router.get("", response_model=ExerciseListResponse)          # GET /exercises
async def list_exercises(
    active_only: bool = Query(default=True, alias="activeOnly"),  # ?activeOnly=true 를 받음
    user: User = Depends(get_current_user),                      # 로그인한 사용자
    db: AsyncSession = Depends(get_db),                          # DB 세션
):
    return await ExerciseService(db).list(user, active_only)    # service 호출만! (얇은 router)
```

여기 등장하는 FastAPI의 핵심 개념 3가지:

- **`@router.get("")`**: "이 함수는 GET 요청을 처리한다"는 표시(데코레이터). `prefix="/exercises"`와 합쳐져 최종 경로가 `/exercises`가 됩니다.
- **`Depends(...)` (의존성 주입)**: FastAPI가 함수 실행 전에 필요한 것(DB 연결, 로그인 사용자)을 **자동으로 만들어 넣어줍니다.** 우리가 직접 DB를 열거나 토큰을 해독할 필요가 없습니다.
  - `Depends(get_db)` → 요청마다 DB 세션을 새로 열어 줌
  - `Depends(get_current_user)` → 요청 헤더의 로그인 토큰을 해독해 "지금 누가 요청했는지" 알려 줌. **`userAvgScore`가 "본인 평균"이려면 사용자가 누구인지 알아야 하므로 꼭 필요**합니다.
- **`response_model=ExerciseListResponse`**: "응답은 이 모양으로 검증·직렬화해라". 이 덕분에 camelCase JSON이 자동으로 나갑니다.

> **`async def`는 무엇?** "비동기 함수"입니다. DB가 응답을 주는 동안 그냥 기다리지 않고, 그 시간에 다른 요청을 처리할 수 있게 합니다. DB를 기다리는 곳마다 `await`을 붙입니다. router·service·repository 함수를 전부 `async def`로 쓰는 게 우리 규칙입니다.

### 5-8. ⑥ main.py — 라우터 등록

마지막으로, 방금 만든 라우터를 앱에 **등록**해야 실제로 동작합니다. 등록하지 않으면 FastAPI는 그런 주소가 있는지조차 모릅니다.

```python
# backend/app/main.py
from app.routers import auth, exercise, users     # exercise 추가

app = FastAPI(title="PoseFit API")
# ...
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(exercise.router, prefix="/api/v1")   # ← 이 줄을 추가
```

- `prefix="/api/v1"`이 라우터의 `prefix="/exercises"`와 합쳐져, **최종 주소는 `/api/v1/exercises`**가 됩니다.
- 이렇게 `/api/v1`을 한 군데서 붙여 명세서의 서버 기준 경로(`servers`)와 맞춥니다.

### 5-9. 백엔드 단독 테스트

코드를 다 만들면 프론트엔드 없이 백엔드만 바로 확인할 수 있습니다. FastAPI는 **자동 문서 페이지**를 제공합니다.

```bash
# backend/ 에서
uv run uvicorn app.main:app --reload      # 서버 실행
```

브라우저로 `http://localhost:8000/docs`에 들어가면, 방금 만든 `GET /exercises`가 목록에 보이고, **"Try it out" 버튼으로 직접 호출**해 볼 수 있습니다. 응답 JSON이 명세서대로 나오는지 눈으로 확인합니다.

---

## 6. 프론트엔드 구현 (Next.js)

이제 백엔드 API는 완성됐습니다. 프론트엔드가 이 API를 호출해 화면에 그리도록 연결합니다.

### 6-1. 핵심 전략 — mock을 먼저, API는 나중에

프론트엔드 화면(`/workout`)은 백엔드가 준비되기 **전에 이미** 만들어져 있었습니다. 어떻게? **가짜 데이터(mock)**를 사용했습니다. `lib/mock/exercises.ts`에 운동 4개를 손으로 적어 두고, 화면은 그걸 불러와 그렸습니다.

핵심은 **가짜 함수와 진짜 함수의 "모양(시그니처)"을 똑같이 맞춰 둔 것**입니다.

```ts
// 가짜(mock)와 진짜(api)가 똑같은 모양
async function getExercises(): Promise<ExerciseListResponse>
```

함수 이름·입력·출력 타입이 같으면, 화면 코드는 **"누가 데이터를 주는지" 신경 쓸 필요가 없습니다.** 그래서 백엔드가 완성된 지금, **단지 불러오는 곳만 mock → api로 바꾸면** 됩니다. 화면 코드(`page.tsx`)는 거의 그대로입니다. 이게 실무에서 프론트와 백엔드가 동시에 일할 수 있는 비결입니다.

### 6-2. 무엇을 만들고 바꾸나

```
frontend/
├ lib/api/
│   ├ types.ts        ← (수정) 운동 타입 추가
│   ├ exercises.ts    ← (신규) 진짜 API 호출 함수
│   └ server.ts       ← (이미 있음) 공통 fetch 도구
└ app/(app)/workout/
    └ page.tsx        ← (수정) import 한 줄만 교체
```

### 6-3. 타입 정의 (types.ts)

타입스크립트는 "이 데이터는 이런 모양이다"를 미리 적어두는 언어입니다. 명세서의 응답 모양을 그대로 옮깁니다.

```ts
// frontend/lib/api/types.ts 에 추가
export type ExerciseType = "static" | "dynamic";

export interface ExerciseSummary {
  id: number;
  nameKo: string;
  nameEn: string | null;
  exerciseType: ExerciseType;
  isActive: boolean;
  userAvgScore: number | null;     // 백엔드가 camelCase로 주므로 여기도 camelCase
}

export interface ExerciseListResponse {
  items: ExerciseSummary[];
}
```

→ 백엔드 schema(`ExerciseSummary`)와 **같은 모양**임에 주목하세요. 백엔드는 파이썬, 프론트는 타입스크립트지만 **명세서라는 같은 약속**을 보고 만들었기 때문에 일치합니다.

### 6-4. 진짜 API 호출 함수 (exercises.ts)

```ts
// frontend/lib/api/exercises.ts
import { apiFetch } from "./server";
import type { ExerciseListResponse } from "./types";

export async function getExercises(): Promise<ExerciseListResponse> {
  return apiFetch("/exercises?activeOnly=true");     // GET /api/v1/exercises 호출
}
```

`apiFetch`는 우리가 미리 만들어 둔 공통 도구로, 실제 네트워크 요청을 보냅니다.

```ts
// frontend/lib/api/server.ts (이미 존재) — 요지만
export const API_BASE = "http://localhost:8000/api/v1";

export async function apiFetch<T>(path, init) {
  const token = (await cookies()).get("accessToken")?.value;  // 로그인 토큰을 쿠키에서 꺼내
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },            // 백엔드에 "나 이 사람이야"라고 전달
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(res.status, ...);
  return await res.json();                                    // JSON을 자바스크립트 객체로
}
```

> **BFF 패턴 / 로그인 토큰**: 백엔드의 `Depends(get_current_user)`가 "누가 요청했는지" 알려면, 프론트가 요청에 **로그인 토큰**을 실어 보내야 합니다. 그 토큰을 `Authorization: Bearer ...` 헤더에 담아 보냅니다. 이게 있어야 백엔드가 **그 사용자의 `userAvgScore`**를 계산할 수 있습니다. 토큰은 안전하게 쿠키에 보관돼 있고, 화면을 그리는 서버 단계에서 꺼내 씁니다.

### 6-5. 화면 연결 — import 한 줄 교체 (page.tsx)

이제 화면이 가짜 대신 진짜 함수를 쓰도록 바꿉니다. **딱 한 줄입니다.**

```diff
// frontend/app/(app)/workout/page.tsx
- import { getExercises, type ExerciseType } from "@/lib/mock/exercises";
+ import { getExercises, type ExerciseType } from "@/lib/api/exercises";
```

화면 코드의 나머지는 **그대로** 둡니다. 함수 모양이 같으니까요.

```tsx
export default async function WorkoutPage() {
  const { items } = await getExercises();    // 진짜 API에서 운동 목록을 받아
  return (
    <ul>
      {items.map((exercise) => (             // 운동마다 카드 하나씩 그림
        <li key={exercise.id}>
          <Link href={`/workout/${exercise.id}`}>
            <p>{exercise.nameKo} <span>{exercise.nameEn}</span></p>
            <p>{exercise.exerciseType === "dynamic" ? "동적" : "정적"}
               {exercise.userAvgScore != null ? ` · 평균 ${exercise.userAvgScore}점` : " · 기록 없음"}</p>
          </Link>
        </li>
      ))}
    </ul>
  );
}
```

> **Server Component(서버 컴포넌트)**: 이 페이지는 `async function`이고 안에서 바로 `await getExercises()`를 합니다. Next.js의 새로운 방식으로, **화면을 브라우저가 아니라 서버에서 미리 그려서** 보내줍니다. 그래서 데이터를 불러오는 코드를 화면 함수 안에 바로 쓸 수 있고, 쿠키의 토큰에도 접근할 수 있습니다.

---

## 7. 전체 흐름 한눈에 — 한 번의 요청을 끝까지 따라가기

사용자가 `/workout` 페이지를 열었을 때, 운동 카드가 뜨기까지 데이터가 흐르는 전체 경로입니다.

```
① 사용자가 브라우저에서 localhost:3000/workout 접속
        │
② Next.js 서버가 WorkoutPage 컴포넌트를 그리기 시작
   → getExercises() 호출
        │
③ apiFetch가 쿠키에서 로그인 토큰을 꺼내,
   GET http://localhost:8000/api/v1/exercises?activeOnly=true 요청 (Authorization 헤더 포함)
        │
   ────────────────────  여기서부터 백엔드(FastAPI)  ────────────────────
        │
④ routers/exercise.py 의 list_exercises 함수가 요청을 받음
   → Depends(get_current_user)가 토큰을 해독해 "이 사용자"를 알아냄
   → Depends(get_db)가 DB 세션을 열어줌
        │
⑤ services/exercise.py 의 list()를 호출
        │
⑥ repositories/exercise.py 가 DB에 질의:
   "노출 중인 운동 전부 + 이 사용자의 운동별 평균 점수(LEFT JOIN)"
        │
⑦ MySQL이 (운동, 평균점수) 목록을 돌려줌
        │
⑧ service가 결과를 ExerciseListResponse(schema)로 변환
   → router의 response_model이 camelCase JSON으로 직렬화
        │
   ────────────────────  다시 프론트엔드(Next.js)  ────────────────────
        │
⑨ apiFetch가 JSON을 받아 자바스크립트 객체로 변환해 반환
        │
⑩ WorkoutPage가 items.map(...)으로 운동마다 카드를 그림
        │
⑪ 완성된 HTML이 브라우저로 전송 → 사용자가 운동 카드 4개를 봄
```

이 한 줄기를 이해하면, 이 프로젝트의 다른 API들도 **전부 같은 구조**임을 알 수 있습니다. 운동 API를 이해했다면 사용자 API, 인증 API도 똑같이 읽을 수 있습니다.

---

## 8. 용어 사전 (빠른 참조)

| 용어 | 뜻 |
|---|---|
| **프론트엔드 / 백엔드** | 화면(사용자가 봄) / 서버(뒤에서 데이터 처리) |
| **API** | 프론트와 백엔드가 약속된 주소로 데이터를 주고받는 창구 |
| **엔드포인트(endpoint)** | API의 개별 주소 한 개 (예: `GET /exercises`) |
| **HTTP 메서드** | 요청의 동사. GET(조회)·POST(생성)·PUT/PATCH(수정)·DELETE(삭제) |
| **JSON** | 데이터를 글자로 표현하는 형식. `{ "key": "value" }` |
| **쿼리 파라미터** | 주소 뒤 `?activeOnly=true` 같은 추가 옵션 |
| **데이터베이스 / MySQL** | 데이터를 영구 저장하는 창고 / 우리가 쓰는 DB 제품 |
| **ORM / SQLAlchemy** | 파이썬 객체로 DB를 다루는 기술 / 우리가 쓰는 ORM 도구 |
| **JOIN** | 두 테이블을 연결해 한 줄로 합치는 것 |
| **LEFT JOIN** | 왼쪽(운동)은 다 보여주고, 짝이 없으면 빈 값으로 채우는 JOIN |
| **FastAPI** | 우리가 쓰는 파이썬 백엔드 프레임워크 |
| **Next.js** | 우리가 쓰는 리액트 기반 프론트엔드 프레임워크 |
| **Pydantic / schema** | API 입출력 데이터의 형식을 정의·검증하는 도구 |
| **모델(model)** | DB 테이블의 파이썬 표현 (schema와 다름) |
| **의존성 주입 / `Depends`** | 함수가 필요로 하는 것(DB·사용자)을 FastAPI가 자동 제공 |
| **async / await** | 기다리는 동안 다른 일을 처리하는 비동기 방식 |
| **mock** | 백엔드가 없을 때 화면을 만들기 위한 가짜 데이터 |
| **camelCase / snake_case** | `nameKo`(JS 방식) / `name_ko`(Python 방식) |
| **토큰(token)** | "내가 누구인지" 증명하는 로그인 표식. 요청 헤더에 실어 보냄 |

---

## 9. 자주 묻는 질문 (FAQ)

**Q. 파일을 왜 이렇게 여러 개로 쪼개나요? 한 파일에 다 쓰면 안 되나요?**
작동은 하지만 프로젝트가 커지면 유지보수가 어려워집니다. 역할별로 나누면(요청받기/로직/DB조회/형식) 각 부분을 따로 이해하고 수정·테스트할 수 있습니다.

**Q. `userAvgScore`는 왜 그냥 컬럼에서 안 가져오나요?**
그건 운동 자체의 속성이 아니라 **"이 사용자가 그 운동을 한 기록의 평균"**이라서, 운동 테이블에 저장돼 있지 않습니다. 운동 기록 통계 테이블과 합쳐(JOIN) 계산해서 만들어냅니다.

**Q. 한 번도 안 한 운동은 목록에 안 나오나요?**
나옵니다. LEFT JOIN을 쓰기 때문에 모든 운동이 나오고, 기록이 없는 운동만 `userAvgScore`가 `null`로 표시됩니다(화면에선 "기록 없음").

**Q. 프론트엔드 화면을 거의 안 바꿨는데 어떻게 진짜 데이터가 나오나요?**
가짜 함수(mock)와 진짜 함수(api)의 모양을 똑같이 맞춰 뒀기 때문입니다. import 경로 한 줄만 바꾸면 화면은 그대로 진짜 데이터를 받습니다.

**Q. 백엔드를 다 만들었는데 화면이 비어 있어요.**
DB의 `exercises` 테이블에 데이터가 들어 있는지 확인하세요. 테이블이 비면 API는 정상이지만 빈 목록을 반환합니다.

---

## 10. 직접 해보기 — 구현 체크리스트

**백엔드 (`backend/`)**
- [ ] `schemas/exercise.py` — 응답 형식 정의
- [ ] `repositories/exercise.py` — 운동 조회 + 평균 점수 LEFT JOIN
- [ ] `services/exercise.py` — 결과를 응답 형식으로 변환
- [ ] `routers/exercise.py` — `GET /exercises` 엔드포인트
- [ ] `main.py` — `app.include_router(exercise.router, prefix="/api/v1")` 등록
- [ ] `uv run uvicorn app.main:app --reload` 후 `http://localhost:8000/docs`에서 테스트

**데이터베이스 (루트)**
- [ ] `docker compose up -d`로 MySQL 기동
- [ ] `docs/seed_exercises.sql`로 운동 데이터 INSERT (`--default-character-set=utf8mb4`)

**프론트엔드 (`frontend/`)**
- [ ] `lib/api/types.ts` — 운동 타입 추가
- [ ] `lib/api/exercises.ts` — 진짜 API 호출 함수 생성
- [ ] `app/(app)/workout/page.tsx` — import를 `lib/mock` → `lib/api`로 교체
- [ ] `npm run dev` 후 `localhost:3000/workout`에서 운동 카드 확인

---

## 참고 자료

- API 명세서: `docs/openapi.yaml` (`/exercises` 항목)
- 백엔드 구조 안내: `backend/README.md`
- DB 스키마: `docs/erd.sql`
- 운동 시드 데이터: `docs/seed_exercises.sql`
- 요구사항: `docs/requirements.md`
- FastAPI 공식 튜토리얼: https://fastapi.tiangolo.com/ko/tutorial/
```
