#!/bin/bash
# mmcv 소스 빌드 스크립트
#
# uv sync 후 이 스크립트를 별도로 실행해야 합니다.
# mmcv는 CUDA Toolkit이 필요해 pyproject.toml에 포함할 수 없습니다.
#
# 사전 조건:
#   - CUDA Toolkit 13.0 설치 (nvcc 필요)
#   - backend/.venv 활성화 상태
#
# 실행 방법:
#   cd backend
#   source .venv/bin/activate
#   bash resource/install_mmcv.sh

set -e

# CUDA 13.0 PATH 설정
export PATH=/usr/local/cuda-13.0/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-13.0/lib64:$LD_LIBRARY_PATH

# nvcc 확인
if ! command -v nvcc &> /dev/null; then
    echo "[ERROR] nvcc를 찾을 수 없습니다."
    echo "  CUDA Toolkit 13.0 설치 필요: sudo apt install cuda-toolkit-13-0"
    echo "  또는 PATH를 확인하세요: export PATH=/usr/local/cuda-13.0/bin:\$PATH"
    exit 1
fi

echo "[INFO] nvcc 버전: $(nvcc --version | grep release)"
echo "[INFO] mmcv 2.1.0 소스 빌드 시작 (10~20분 소요)..."

pip install --no-build-isolation "mmcv==2.1.0" \
    -f https://download.openmmlab.com/mmcv/dist/cu130/torch2.12.0/index.html

echo "[INFO] 설치 확인..."
python -c "import mmcv; print(f'mmcv {mmcv.__version__} 설치 완료')"
