# PoseFit 백엔드 (FastAPI + ML) — CPU 전용 단일 스테이지 이미지.
# dlib/opencv/mediapipe 등 네이티브 의존성 때문에 멀티스테이지 대신 단일 스테이지로 안정성 우선.
#
# ⚠️ mediapipe·torch·dlib 는 x86_64 휠만 제공 → 반드시 linux/amd64 로 빌드한다.
#    (compose 의 platform: linux/amd64, 또는 docker build --platform linux/amd64)
FROM python:3.11-slim

# uv (의존성 설치 도구) — extra-build-dependencies(chumpy=pip) 지원 위해 최신 사용
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 시스템 의존성
#  - dlib(face-recognition) 빌드: build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
#  - opencv/mediapipe 런타임: libgl1 libglib2.0-0
#  - cv2 비디오 디코딩: ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libopenblas-dev \
        liblapack-dev \
        libx11-dev \
        libgtk-3-dev \
        libgl1 \
        libglib2.0-0 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 의존성 레이어 캐시 — lock/pyproject 변경 없으면 재설치 생략
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 앱 소스 복사 후 최종 동기화
COPY . .
RUN uv sync --frozen --no-dev \
    && sed -i 's/\r$//' docker-entrypoint.sh \
    && chmod +x docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
