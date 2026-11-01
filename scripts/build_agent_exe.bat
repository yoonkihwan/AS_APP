@echo off
chcp 65001 > nul
echo =======================================================
echo  🚀 바코드 에이전트 단일 EXE 빌드 스크립트 (PyInstaller)
echo =======================================================
echo.

REM 가상환경 파이썬 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [X] 파이썬이 시스템에 설치되어 있지 않습니다.
    pause
    exit /b 1
)

echo [*] PyInstaller 설치 확인 중...
pip install pyinstaller --quiet

echo [*] barcode_agent.exe 빌드 시작 (단일 파일, 아이콘 및 의존성 압축)...
pyinstaller --noconfirm --onedir --windowed --name "barcode_agent" --clean "scripts\barcode_agent.py"

if %errorlevel% equ 0 (
    echo.
    echo =======================================================
    echo  ✅ 빌드 완료!
    echo  위치: dist\barcode_agent\barcode_agent.exe
    echo  현장 PC에는 dist\barcode_agent 폴더 전체를 복사해서 쓰시면 됩니다!
    echo =======================================================
) else (
    echo.
    echo [X] 빌드 도중 오류가 발생했습니다.
)
pause
