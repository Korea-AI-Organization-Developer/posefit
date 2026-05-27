# PoseFit

AI 기반 운동 자세 분석 및 피드백 웹 서비스

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| 프론트엔드 | Next.js 16, TypeScript, TailwindCSS |
| 백엔드 | FastAPI, SQLAlchemy, Alembic |
| 데이터베이스 | MySQL 8.0 |
| 패키지 관리 | uv (백엔드), npm (프론트엔드) |
| 인프라 | Docker |

---

## 시작하기

### 사전 준비
- Python 3.11
- Node.js 18 이상
- Docker Desktop
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd PoseFit-SemiColons
```

### 2. 환경변수 설정

```bash
# 루트 (Docker MySQL 설정)
cp .env.example .env

# 백엔드 (FastAPI 설정)
cp backend/.env.example backend/.env
```

`.env`, `backend/.env` 파일을 열어 값을 채운다.

### 3. Docker MySQL 실행

```bash
docker compose up -d
```

### 4. 백엔드 실행

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

→ `http://localhost:8000`
→ API 문서: `http://localhost:8000/docs`

### 5. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

→ `http://localhost:3000`
