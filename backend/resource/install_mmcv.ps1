# mmcv 소스 빌드 스크립트 (Windows)
#
# 사전 조건:
#   - CUDA Toolkit 13.0 설치 (https://developer.nvidia.com/cuda-downloads)
#   - Visual C++ Build Tools 설치 (install_face_recognition.ps1 먼저 실행)
#   - backend\.venv 활성화 상태
#
# 실행 방법 (PowerShell):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\.venv\Scripts\Activate.ps1
#   .\resource\install_mmcv.ps1

$ErrorActionPreference = "Stop"

# nvcc 확인
if (-not (Get-Command nvcc -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] nvcc를 찾을 수 없습니다."
    Write-Host "  CUDA Toolkit 13.0 설치 필요: https://developer.nvidia.com/cuda-downloads"
    Write-Host "  설치 후 시스템 PATH에 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin' 추가"
    exit 1
}

$nvccVersion = nvcc --version | Select-String "release"
Write-Host "[INFO] nvcc 버전: $nvccVersion"
Write-Host "[INFO] mmcv 2.1.0 소스 빌드 시작 (10~20분 소요)..."

pip install --no-build-isolation "mmcv==2.1.0" `
    -f https://download.openmmlab.com/mmcv/dist/cu130/torch2.12.0/index.html

Write-Host "[INFO] 설치 확인..."
python -c "import mmcv; print(f'mmcv {mmcv.__version__} 설치 완료')"
