@echo off
chcp 65001 > nul
echo =======================================================
echo  🚀 사내 AS / 툴 입출고 관리 로컬 서버 원클릭 실행기
echo =======================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [X] 오류: venv 가상환경을 찾을 수 없습니다!
    pause
    exit /b 1
)

echo [*] 가상환경 (venv) 확인 완료
echo [*] Django 로컬 서버(포트 8001) 구동 시작...
echo.
echo  👉 포탈 메인: http://127.0.0.1:8001/
echo  👉 툴 관리 대시보드: http://127.0.0.1:8001/inventory/
echo  👉 ⚡ 바코드 입출고: http://127.0.0.1:8001/inventory/barcode-manage/
echo.
echo =======================================================
echo  서버를 중지하려면 이 창에서 Ctrl + C 를 누르십시오.
echo =======================================================
echo.

venv\Scripts\python.exe manage.py runserver 8001
pause
