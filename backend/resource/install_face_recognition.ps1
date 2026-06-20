# face-recognition (dlib) 시스템 의존성 설치 스크립트 (Windows)
#
# 실행 방법 (PowerShell 관리자 권한):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\resource\install_face_recognition.ps1

$ErrorActionPreference = "Stop"

Write-Host "[INFO] dlib 빌드에 필요한 도구를 설치합니다..."

# CMake 설치 확인
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] CMake 설치 중..."
    winget install --id Kitware.CMake --silent --accept-package-agreements --accept-source-agreements
} else {
    Write-Host "[OK] CMake 이미 설치됨: $(cmake --version | Select-Object -First 1)"
}

# Visual C++ Build Tools 확인 (cl.exe)
if (-not (Get-Command cl -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] Visual C++ Build Tools 설치 중 (시간이 걸릴 수 있습니다)..."
    winget install --id Microsoft.VisualStudio.2022.BuildTools --silent --accept-package-agreements --accept-source-agreements `
        --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    Write-Host "[INFO] 설치 완료 후 터미널을 재시작하세요."
} else {
    Write-Host "[OK] Visual C++ Build Tools 이미 설치됨"
}

Write-Host ""
Write-Host "[INFO] 설치 완료. 이제 'uv sync'를 실행하면 face-recognition(dlib)이 빌드됩니다."
Write-Host "[주의] Visual C++를 새로 설치했다면 터미널을 재시작한 후 uv sync 하세요."
