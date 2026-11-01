@echo off
chcp 65001 > nul
cd /d "%~dp0.."

echo =======================================================
echo  [AS-APP] 바코드 에이전트 다른 PC 배포용 EXE 빌드
echo =======================================================
echo.

set PYTHON_EXE=venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [*] PyInstaller 설치 확인 중...
"%PYTHON_EXE%" -m pip install pyinstaller --quiet

echo [*] barcode_agent.exe 단일 파일(무창 백그라운드) 빌드 중...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onefile --noconsole --name "barcode_agent" --clean "scripts\barcode_agent.py"

if %errorlevel% equ 0 (
    if not exist "dist\barcode_agent_pack" mkdir "dist\barcode_agent_pack"
    if exist "dist\barcode_agent_pack\시작프로그램_자동등록.bat" del /f /q "dist\barcode_agent_pack\시작프로그램_자동등록.bat"
    copy /y "dist\barcode_agent.exe" "dist\barcode_agent_pack\barcode_agent.exe" > nul
    (
        echo [SETTINGS]
        echo server_url = https://cheng-1.com
        echo max_key_interval_sec = 0.065
        echo min_serial_length = 4
        echo beep_on_scan = True
    ) > "dist\barcode_agent_pack\agent_config.ini"

    echo.
    echo =======================================================
    echo  빌드 완료!
    echo  배포 폴더: dist\barcode_agent_pack
    echo  안의 파일들을 다른 PC에 복사하십시오.
    echo =======================================================
) else (
    echo.
    echo [X] 빌드 도중 오류가 발생했습니다.
)
pause
