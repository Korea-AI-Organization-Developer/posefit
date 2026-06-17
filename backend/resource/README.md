# backend/resource — 추가 설치 가이드

`uv sync`만으로는 설치할 수 없는 패키지들의 설치 스크립트 모음.

---

## Linux / macOS

```bash
# 1. 시스템 의존성 설치 (최초 1회)
bash resource/install_face_recognition.sh

# 2. Python 패키지 설치
uv sync

# 3. mmcv 소스 빌드 (CUDA 필요, 10~20분)
source .venv/bin/activate
bash resource/install_mmcv.sh
```

---

## Windows

PowerShell을 **관리자 권한**으로 실행 후:

```powershell
# 실행 정책 허용 (현재 세션만)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 1. 시스템 의존성 설치 (최초 1회, 터미널 재시작 필요)
.\resource\install_face_recognition.ps1

# 2. Python 패키지 설치
uv sync

# 3. mmcv 소스 빌드 (CUDA 필요, 10~20분)
.\.venv\Scripts\Activate.ps1
.\resource\install_mmcv.ps1
```

---

## 스크립트 목록

| 스크립트 | OS | 설명 |
|----------|----|------|
| `install_face_recognition.sh` | Linux/macOS | dlib 빌드용 시스템 패키지 (cmake 등) |
| `install_face_recognition.ps1` | Windows | CMake + Visual C++ Build Tools |
| `install_mmcv.sh` | Linux/macOS | mmcv==2.1.0 CUDA 소스 빌드 |
| `install_mmcv.ps1` | Windows | mmcv==2.1.0 CUDA 소스 빌드 |

---

## 패키지별 설명

### face-recognition / dlib
`dlib`은 C++로 작성되어 빌드 도구가 필요합니다.  
`uv sync` 전에 반드시 설치 스크립트를 먼저 실행하세요.

- **Linux**: cmake, build-essential, libopenblas-dev 등
- **Windows**: CMake + Visual C++ Build Tools (winget으로 자동 설치)

### mmcv
CUDA Toolkit 버전과 PyTorch 빌드 버전이 일치해야 소스 빌드 가능.  
현재 환경: `torch 2.12.0+cu130` → CUDA Toolkit 13.0 필요.

- **CUDA Toolkit 설치**
  - Linux: `sudo apt install cuda-toolkit-13-0`
  - Windows: https://developer.nvidia.com/cuda-downloads
