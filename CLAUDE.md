# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PoseFit — AI 기반 운동 자세 분석·피드백 웹 서비스. 사용자가 웹캠으로 운동하면 포즈 추정(ViTPose-Base)으로 관절 키포인트를 추출하고, 정답 영상과 비교해 점수·피드백을 제공한다.

**모노레포 구성**
- `backend/` — FastAPI + SQLAlchemy(async) + Alembic. 패키지 관리는 **uv**
- `frontend/` — Next.js 16 + React 19 + TailwindCSS v4. 패키지 관리는 **npm**
- `docs/` — ERD(`erd.sql`), 요구사항(`requirements.md`), Git 컨벤션(`git_convention.md`), API 명세(`openapi.yaml`), 와이어프레임
- `docker-compose.yaml` — 개발용 MySQL 8.0

## 작업 언어

문서·주석·커밋 메시지·PR은 **한국어**로 작성한다 (기존 코드베이스 전체가 한국어 기준).

## 자주 쓰는 명령어

**DB (루트에서)**
```bash
docker compose up -d        # MySQL 8.0 컨테이너 기동 (utf8mb4)
```

**백엔드 (`backend/`에서)**
```bash
uv sync                                          # 의존성 설치
uv run alembic upgrade head                      # DB 테이블 생성/마이그레이션 적용
uv run uvicorn app.main:app --reload             # 개발 서버 (http://localhost:8000, 문서 /docs)
```

**프론트엔드 (`frontend/`에서)**
```bash
npm install
npm run dev                 # http://localhost:3000
npm run build               # 프로덕션 빌드
```

> 테스트·린트 도구는 아직 설정돼 있지 않다. 임의로 `pytest`/`ruff`/`eslint` 명령을 가정하지 말 것.

## 백엔드 아키텍처 (레이어드)

요청 흐름: **routers → services → repositories → models**, 입출력은 schemas로 검증/직렬화.
전체 가이드와 새 기능 추가 예시는 [backend/README.md](backend/README.md) 참고. 반드시 지킬 규칙:

- **routers는 얇게** — 입력 받아 service 호출만. 비즈니스 로직 금지.
- **commit은 services에서만** — repositories는 조회/추가까지만 하고 `commit` 하지 않는다.
- **models ≠ schemas** — models는 DB 테이블(SQLAlchemy), schemas는 API 입출력(Pydantic). 섞지 않는다.
- 모든 router/service/repository 함수는 `async def`, DB 세션은 `Depends(get_db)`로 주입.
- 라우터 등록은 `app/main.py`에서 `app.include_router(..., prefix="/api")`.

**현재 상태**: `models/`만 `docs/erd.sql` 기준으로 채워져 있고 `schemas/` `repositories/` `services/` `routers/`는 빈 패키지다. 기능 담당자가 도메인명으로 파일을 추가한다.

**AI/비전 코드**는 `backend/ai/`에 모은다 (`face/`, `pose/`, 그리고 추가 예정인 `rag/`).

## 데이터베이스 & Alembic

- MySQL 8.0, **async 드라이버(aiomysql)** 사용. 커넥션 URL은 `backend/.env`의 `DATABASE_URL`.
- **새 모델을 만들면 반드시 `app/models/__init__.py`에 import**해야 Alembic autogenerate가 인식한다.
- 모델 변경 후:
  ```bash
  uv run alembic revision --autogenerate -m "변경 내용"
  uv run alembic upgrade head
  ```
- **생성된 `alembic/versions/*.py`는 반드시 git에 커밋**한다 (팀원이 `upgrade head`로 동일 스키마를 받는 핵심).
- 공통 패턴: 타임스탬프는 `models/mixins.py`의 `TimestampMixin`, ENUM은 `models/enums.py`의 `str` Enum 사용.
- **1:1 관계**는 자식 테이블의 `user_id`를 PK로 두고(`primary_key=True`) 부모 쪽 relationship에 `uselist=False`를 준다. ERD 시각화 도구는 이를 1:N으로 잘못 그리므로 DDL/모델 코드를 신뢰한다.

## 프론트엔드

- **중요**: 이 프로젝트의 Next.js는 16 버전으로, 학습 데이터의 Next.js와 API·구조가 다를 수 있다. 코드 작성 전 `node_modules/next/dist/docs/`의 관련 가이드를 먼저 확인한다 ([frontend/AGENTS.md](frontend/AGENTS.md) 참고).
- App Router 사용 (`app/` 디렉토리).

## Git 컨벤션

전체 규칙은 [docs/git_convention.md](docs/git_convention.md). 요약:

- **커밋/PR 제목**: `type: subject` (feat·fix·docs·style·refactor·test·chore), 마침표 없이 명령조.
- **브랜치**: `type/subject-#issue_number` (예: `feat/payment-#12`).
- **흐름**: 이슈 생성 → 브랜치 분기 → PR 본문에 `Closes #이슈번호`. 작업은 `develop`에서 분기해 `develop`으로 머지(merge commit). `main`·`develop`은 직접 push 금지(PR 필수).
