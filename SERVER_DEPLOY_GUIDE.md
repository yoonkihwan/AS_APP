# 🚀 메인 서버(라즈베리파이) 배포 및 업데이트 가이드

이 문서는 로컬 개발 환경(Windows)에서 기능 수정/추가 후, 실제 서비스 중인 **메인 운영 서버(라즈베리파이 / `cheng-1.com`)**에 최신 버전을 안전하게 배포하고 업데이트하는 표준 절차서입니다.

---

## 📌 1. 시스템 환경 개요

| 구분 | 로컬 개발 환경 (내 PC) | 메인 운영 서버 (라즈베리파이) |
| :--- | :--- | :--- |
| **운영체제** | Windows 11 | Debian GNU/Linux 13 (Pi-Server) |
| **실행 위치** | `C:\Users\rlao1\AS_APP` | `/home/cheng/AS_APP` |
| **가상환경** | `.\venv\Scripts\python.exe` | `source venv/bin/activate` |
| **PostgreSQL 포트** | **`5433`** (OS 자동 판별) | **`5432`** (OS 자동 판별) |
| **웹 접속 주소** | `http://127.0.0.1:8001/` (로컬 테스트용) | **`https://cheng-1.com`** (실서비스 운영용) |
| **외부 터널** | Cloudflare Tunnel (임시 테스트용) | Cloudflare Tunnel (고정 도메인 연결) |

---

## 🔄 2. 표준 업데이트 2단계 절차

코드 수정 후 메인 서버에 반영할 때는 반드시 **[1단계: 내 PC]** ➔ **[2단계: 메인 서버]** 순서로 진행합니다.

### [1단계] 로컬 개발 PC (Windows)에서 작업

로컬에서 기능 개발 및 `http://127.0.0.1:8001/` 테스트를 완료한 후 GitHub 저장소로 푸시합니다.

```powershell
# 1. 변경된 파일 확인
git status

# 2. 변경사항 스테이징 및 커밋
git add .
git commit -m "feat/fix: 작업 내용 요약"

# 3. GitHub 원격 저장소(origin/main)로 푸시
git push origin main
```

---

### [2단계] 메인 서버 (라즈베리파이)에서 반영

라즈베리파이 화면(또는 SSH 터미널)에서 아래 명령어를 순서대로 실행합니다.

```bash
# 1. 프로젝트 폴더로 이동
cd ~/AS_APP

# 2. GitHub에서 최신 코드 내려받기
git pull origin main

# 3. ⭐️ 가상환경 활성화 (필수! 누락 시 No module named 'django' 발생)
source venv/bin/activate
# (정상 활성화 시 프롬프트 맨 앞에 '(venv)' 표시 생성됨)

# 4. DB 마이그레이션 (DB 모델이나 필드가 변경된 경우 필수)
python manage.py migrate

# 5. 특수 일괄 작업 스크립트 실행 (필요한 경우에만 실행)
# 예: python mark_legacy_data.py

# 6. 정적 파일 수집 (CSS, JS, 폰트 등 정적 리소스 변경 시)
python manage.py collectstatic --noinput

# 7. 웹 서비스 프로세스 재시작
sudo systemctl restart as_app
```

> [!TIP]
> 만약 백그라운드 서비스명이 기억나지 않거나 프로세스가 꼬였을 때는 간단하게 **`sudo reboot`** 로 라즈베리파이를 재부팅해도 부팅 시 모든 서비스가 최신 상태로 자동 구동됩니다.

---

## ⚡️ 3. 빠른 업데이트 한 줄 복사본 (라즈베리파이 터미널용)

일반적인 소스코드 수정(버그 수정, UI 변경 등) 시 라즈베리파이에서 아래 한 줄을 복사하여 실행하면 한 번에 끝납니다:

```bash
cd ~/AS_APP && git pull origin main && source venv/bin/activate && python manage.py migrate && python manage.py collectstatic --noinput && sudo systemctl restart as_app
```

---

## 🚨 4. 트러블슈팅 (자주 발생하는 오류 및 대처법)

### Q1. `ModuleNotFoundError: No module named 'django'`
* **원인**: 파이썬 가상환경(`venv`)을 켜지 않고 시스템 파이썬(`python3`)으로 직접 실행했을 때 발생합니다.
* **해결**: 반드시 `source venv/bin/activate`를 먼저 입력하여 `(venv)` 상태에서 `python manage.py ...`를 실행하세요.

---

### Q2. `EXT4-fs (sda2): shut down requested` / `cd: Input/output error` / `command not found`
* **원인**: USB 외장 SSD 또는 SD카드의 전원 부족, 케이블 접촉 불량으로 인해 리눅스 커널이 디스크 연결을 안전상 강제 차단(Shut down)한 상태입니다. 디스크가 끊겼으므로 `git`, `sudo`, `whoami` 등 디스크에 저장된 모든 명령어가 `command not found`로 뜹니다.
* **해결**:
  1. 라즈베리파이에 연결된 USB 저장장치 케이블을 꽉 다시 꽂습니다.
  2. 라즈베리파이 **전원 케이블을 뽑고 5초 후 다시 꽂아 재부팅(콜드 리부트)**합니다.
  3. 부팅 후 `My IP address is 192.168.X.X` 정상 IP가 뜨는지 확인하고 작업을 재개합니다.

---

### Q3. 윈도우(내 PC) 터미널에서 `python` 치면 아무 반응 없이 `Python` 글자만 뜨고 종료되는 경우
* **원인**: 윈도우 스토어 앱 실행 별칭(stub)이 호출된 상태입니다.
* **해결**: 가상환경 경로를 직접 지정하여 실행합니다:
  ```powershell
  .\venv\Scripts\python.exe manage.py runserver 8001
  ```

---

### Q4. DB 접속 포트 충돌 방지 원리
* 본 프로젝트는 [`as_project/settings.py`](file:///c:/Users/rlao1/AS_APP/as_project/settings.py#L102-L108)에서 OS를 자동 감지하도록 설정되어 있습니다:
  * **Windows (내 PC)**: 포트 `5433` 자동 사용
  * **Linux (라즈베리파이)**: 포트 `5432` 자동 사용
* 따라서 로컬과 운영 서버 간에 DB 포트 설정을 매번 수동으로 변경할 필요 없이 그대로 배포하시면 됩니다.
