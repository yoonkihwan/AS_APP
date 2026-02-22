# Cloudflare Tunnel을 이용한 로컬 서버 임시 배포/공유 가이드

이 문서는 내 컴퓨터에서 개발 중인 로컬 웹 서버(Django)를 외부(인터넷)에서 누구나 임시로 접속해 볼 수 있게 열어주는 **Cloudflare Tunnel (trycloudflare)** 사용 방법을 설명합니다.

---

## 🚀 빠르게 실행하는 방법 (요약)

Cloudflare Tunnel을 사용하려면 **터미널(Terminal) 창이 2개** 필요합니다. 각각의 터미널에 아래 명령어를 실행하세요.

### 터미널 1: Django 웹 서버 실행
먼저 웹 어플리케이션(서버)을 켭니다. 구동 시 포트번호는 기본 8000번입니다.

```powershell
# 1. 가상환경 활성화
.\venv\Scripts\activate

# 2. 서버 구동
python manage.py runserver
```

### 터미널 2: Cloudflare Tunnel 실행
위에서 켠 서버(8000포트)를 외부로 연결해주는 터널을 켭니다. (Node.js의 `npx` 명령어 사용)

```powershell
# 터널 구동 (포트 8000을 대상)
npx cloudflared tunnel --url http://localhost:8000
```

* 위 명령어를 입력하면 터미널 화면 중간쯤에 `your url is: https://XXXXX.trycloudflare.com` 형태의 임시 주소가 생성되어 나타납니다.
* 이 주소를 복사해서 다른 사람들에게 공유하면 됩니다.

---

## 🚦 꼭 알아두어야 할 점 (주의사항)

1. **서버와 터널은 항상 켜져 있어야 합니다.**
   - 두 개의 터미널 중 하나라도 끄거나 `Ctrl + C`를 눌러 중단하면 외부 접속이 단절됩니다.
2. **PC가 절전 모드에 들어가면 안 됩니다.**
   - 컴퓨터가 절전 모드로 진입하면 통신이 끊어지게 되어 임시 서버가 다운됩니다.
   - 외부 사람에게 접속을 허용하는 동안에는 윈도우 전원 관리 설정에서 **'절전 모드'를 '안 함'**으로 변경해 두시거나, 마우스를 한 번씩 움직여 절전 모드를 방지하세요. 데스크탑의 경우 모니터 화면만 꺼지는 것은 상관없습니다.
3. **주소는 매번 바뀝니다.**
   - Cloudflare Tunnel 명령어를 새로 실행할 때마다 `https://...trycloudflare.com` 이라는 임시 주소는 매번 다른 주소로 생성됩니다. 만약 터널을 재시작했다면 바뀐 주소를 다시 알려주어야 합니다.
4. **보안 유의**
   - 불특정 다수가 알면 서버 자원을 소모하거나 의도치 않은 행위를 할 수 있으므로, 보여주고자 하는 분들에게만 주소를 안내하세요.

---

## 🛠 `settings.py` 사전 설정 (참고용)

서버 코드가 Cloudflare의 임시 도메인 요청을 받아들일 수 있도록 Django의 `as_project/settings.py` 내 `CSRF_TRUSTED_ORIGINS` 설정은 다음과 같이 되어 있어야 합니다. (현재 이미 설정되어 있습니다.)

```python
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://*.trycloudflare.com",    # 이 부분이 Cloudflare 터널을 위해 필요합니다!
    "https://*.loca.lt",
]
```
