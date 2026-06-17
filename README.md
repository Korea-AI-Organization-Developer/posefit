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
- **dlib 빌드 도구** — 얼굴 인식 라이브러리(dlib) 빌드에 필요. `uv sync` 전에 설치한다.
  - macOS: `brew install cmake` (Xcode Command Line Tools는 대부분 이미 설치됨)
  - Windows: 클론 후 별도 스크립트로 설치 (아래 2-1단계 참고)
  - Linux: `sudo apt install cmake build-essential libopenblas-dev liblapack-dev`

### 1. 저장소 클론

```bash
git clone https://github.com/Korea-AI-Organization-Developer/posefit.git
cd posefit
```

### 1-1. (Windows 전용) 얼굴 인식 의존성 설치

PowerShell을 **관리자 권한**으로 열고 실행한다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\resource\install_face_recognition.ps1
```

### 1-2. (Linux 전용) 얼굴 인식 의존성 설치

```bash
bash resource/install_face_recognition.sh
```

### 2. 환경변수 설정

```bash
# macOS / Linux
cp .env.example .env
cp backend/.env.example backend/.env
```

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
```

```powershell
# Windows (CMD)
copy .env.example .env
cd backend
copy .env.example .env
cd ..
```

각 `.env` 파일을 열어 주석을 읽고 값을 채운다. 아래 항목만 주의한다.

- **`DATABASE_URL`** — 루트 `.env`에 설정한 `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE`와 일치해야 한다.
- **`JWT_SECRET_KEY`** — 외부에서 받는 값이 아니다. 아래 명령으로 직접 생성해서 붙여넣는다.
  ```bash
  # macOS / Linux
  openssl rand -hex 32
  ```
  ```powershell
  # Windows (PowerShell)
  -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
  ```
- **`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`** — Google Cloud Console에서 발급.

### 3. Docker MySQL 실행

> **실행 전 확인** — `.env`(루트)와 `backend/.env`의 DB 정보가 일치해야 한다.
>
> | 루트 `.env` | `backend/.env` `DATABASE_URL` |
> |---|---|
> | `MYSQL_USER=posefit` | URL의 사용자명 |
> | `MYSQL_PASSWORD=...` | URL의 비밀번호 |
> | `MYSQL_DATABASE=posefitdb` | URL의 DB명 |
>
> 예: `DATABASE_URL=mysql+aiomysql://posefit:비밀번호@localhost:3306/posefitdb`
>
> 값이 다르면 컨테이너가 떠도 접속이 거부된다. 틀렸다면 지금 수정하고 진행한다.

```bash
docker compose up -d
```

### 4. 데이터베이스 마이그레이션

```bash
cd backend
uv sync        # dlib 컴파일 포함 — cmake가 없으면 실패하므로 사전 준비 항목 확인
uv run alembic upgrade head
```

이 명령어 한 번으로 MySQL에 모든 테이블이 생성된다.

> **Alembic이란?**
> SQLAlchemy 모델(Python 코드)과 실제 DB 테이블 사이의 변경사항을 추적·적용하는 마이그레이션 도구다.
>
> - `alembic/versions/` — 마이그레이션 파일들이 쌓이는 폴더. 각 파일에 "이 시점에 어떤 테이블/컬럼을 추가·변경·삭제했는지"가 기록된다.
> - `alembic_version` 테이블 — Alembic이 DB 안에 자동으로 만드는 테이블. "이 DB는 어느 버전까지 적용됐는지" 버전 ID 하나만 저장한다.
> - `upgrade head` — 현재 DB 버전부터 최신 마이그레이션까지 순서대로 전부 적용한다. DB가 비어있으면 처음부터 전부 실행되므로 최초 세팅 때도 이 명령어 하나면 된다.
>
> 앞으로 모델을 수정했다면:
> ```bash
> uv run alembic revision --autogenerate -m "변경 내용 설명"  # 마이그레이션 파일 자동 생성
> uv run alembic upgrade head                                 # DB에 적용
> ```
> 생성된 파일은 반드시 git에 커밋해야 팀원들도 `upgrade head`로 반영받을 수 있다.

### 5. 백엔드 실행

```bash
cd backend
uv run uvicorn app.main:app --reload
```

→ `http://localhost:8000`
→ API 문서: `http://localhost:8000/docs`

### 6. 프론트엔드 실행

```bash
cd frontend
cp .env.example .env   # NEXT_PUBLIC_GOOGLE_CLIENT_ID 를 채운다(구글 로그인용)
npm install
npm run dev
```

`.env.local` — `NEXT_PUBLIC_API_BASE_URL`(기본값 그대로면 OK)과 `NEXT_PUBLIC_GOOGLE_CLIENT_ID`(`backend/.env`의 `GOOGLE_CLIENT_ID`와 동일 값)를 설정한다. 구글 로그인을 쓰지 않으면 비워둬도 화면은 뜬다.

→ `http://localhost:3000`

---

## 트러블슈팅

### Docker MySQL 접속 거부 (Access denied)

```
pymysql.err.OperationalError: (1045, "Access denied for user 'posefit'@'...'")
```

`MYSQL_USER` / `MYSQL_PASSWORD` 환경변수는 볼륨이 **처음 생성될 때만** 적용된다.
`.env` 값을 변경했거나 볼륨이 이전 설정으로 초기화된 경우 볼륨을 삭제하고 재생성해야 한다.

```bash
# 루트에서 실행 — DB 데이터가 전부 삭제되므로 개발 초기에만 사용
docker compose down -v
docker compose up -d
```

이후 `uv run alembic upgrade head`를 다시 실행하면 스키마가 새로 생성된다.

### Alembic multiple heads 오류

```
FAILED: Multiple head revisions are present for given argument 'head'
```

팀원들이 같은 부모 리비전에서 각각 마이그레이션을 만들면 브랜치가 생긴다. merge 리비전을 생성해 합친다.

```bash
uv run alembic heads                          # 현재 head 두 개 확인
uv run alembic merge -m "merge branches" <rev1> <rev2>
uv run alembic upgrade head
```

생성된 merge 파일은 반드시 git에 커밋해야 팀원들도 동일하게 적용받는다.
