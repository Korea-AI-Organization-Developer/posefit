#!/bin/bash
# face-recognition (dlib) 시스템 의존성 설치 스크립트
#
# face-recognition은 dlib을 사용하며, dlib은 C++ 빌드가 필요합니다.
# uv sync 전에 이 스크립트를 먼저 실행하세요.
#
# 실행 방법:
#   bash resource/install_face_recognition.sh

set -e

echo "[INFO] dlib 빌드에 필요한 시스템 패키지 설치 중..."

sudo apt update
sudo apt install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev

echo "[INFO] 시스템 패키지 설치 완료"
echo "[INFO] 이제 'uv sync'를 실행하면 face-recognition(dlib)이 빌드됩니다."
