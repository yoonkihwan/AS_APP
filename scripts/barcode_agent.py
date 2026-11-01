"""
=============================================================================
바코드 스캐너 백그라운드 감지 에이전트 (Barcode Background Agent)
=============================================================================
- 모델: MQ160W 미라클 스캐너 (또는 모든 표준 USB HID 바코드 스캐너)
- 환경: Windows 10 / 11 (Python 표준 ctypes 기반, 추가 라이브러리 설치 불필요)
- 동작:
    1. 백그라운드에서 키보드 스트림 인터벌(35ms 미만)을 실시간 감시
    2. 일반 사용자 타건(100ms+) 및 복사/붙여넣기는 100% 무시
    3. 스캐너의 고속 입력 후 Enter가 감지되면 즉시 브라우저 팝업
    4. http://<서버주소>/inventory/quick-scan/?serial=<시리얼> 로 즉시 이동
    5. 인식 성공 시 비프음(Beep) 청각 피드백 제공
=============================================================================
"""

import sys
import os
import time
import ctypes
from ctypes import wintypes
import webbrowser
import configparser
import winsound
import threading

# Windows 콘솔 출력 인코딩 안전화
try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ── 1. 기본 설정 (config.ini가 있으면 불러오고, 없으면 기본값 사용) ──
DEFAULT_CONFIG = {
    "SERVER_URL": "https://cheng-1.com",
    "MAX_KEY_INTERVAL_SEC": "0.065",   # 65ms 이하를 바코드 입력으로 판정
    "MIN_SERIAL_LENGTH": "4",          # 최소 4자리 이상
    "BEEP_ON_SCAN": "True",            # 스캔 성공 시 삡! 비프음
}

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "agent_config.ini")

def load_or_create_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding="utf-8")
        except Exception:
            pass
    if "SETTINGS" not in config:
        config["SETTINGS"] = DEFAULT_CONFIG
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception:
            pass
    return config["SETTINGS"]

CONFIG = load_or_create_config()
SERVER_URL = CONFIG.get("SERVER_URL", "http://127.0.0.1:8001").rstrip("/")
MAX_INTERVAL = float(CONFIG.get("MAX_KEY_INTERVAL_SEC", "0.040"))
MIN_LENGTH = int(CONFIG.get("MIN_SERIAL_LENGTH", "4"))
BEEP_ENABLED = CONFIG.get("BEEP_ON_SCAN", "True").lower() == "true"

# ── 2. Win32 Low-Level Keyboard Hook 정의 ──
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_RETURN = 0x0D

# 키보드 구조체
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK

user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL

user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t

user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL


# ── 3. 바코드 버퍼 및 판별 로직 ──
class BarcodeCollector:
    def __init__(self):
        self.buffer = []
        self.last_time = 0.0
        self.intervals = []

    def process_key(self, char, is_enter=False):
        now = time.perf_counter()

        if is_enter:
            # 엔터 입력 시: 수집된 버퍼 검증
            if len(self.buffer) >= MIN_LENGTH:
                # 버퍼 내 평균 또는 최대 간격 체크
                max_gap = max(self.intervals) if self.intervals else 0.0
                if max_gap <= MAX_INTERVAL:
                    serial = "".join(self.buffer).strip()
                    self.reset()
                    return serial
            self.reset()
            return None

        # 일반 문자 입력 시
        if not self.buffer:
            # 첫 글자
            self.buffer.append(char)
            self.last_time = now
            self.intervals = []
        else:
            interval = now - self.last_time
            self.last_time = now
            if interval <= MAX_INTERVAL:
                # 초고속 연속 타건 -> 바코드 의심 스트림으로 누적
                self.buffer.append(char)
                self.intervals.append(interval)
            else:
                # 간격 초과 (사람의 일반 타건) -> 버퍼 초기화 후 현재 글자부터 다시 시작
                self.buffer = [char]
                self.intervals = []

        return None

    def reset(self):
        self.buffer = []
        self.intervals = []
        self.last_time = 0.0

collector = BarcodeCollector()

def is_inventory_form_active():
    """현재 최상단 활성 창이 입고 등록 또는 출고 등록 '작성 폼(추가 화면)'인지 검사"""
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return False
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value.lower()
        # 대시보드, 목록, 이력 등은 폼이 아니므로 제외!
        # 오직 입출고 등록 '추가' 화면일 때만 폼 내부 연속 입력으로 판정
        form_keywords = ["입고 등록 추가", "출고 등록 추가", "inventorybatch/add", "outboundbatch/add"]
        return any(kw in title for kw in form_keywords)
    except Exception:
        return False

CHO = ['r', 'R', 's', 'e', 'E', 'f', 'a', 'q', 'Q', 't', 'T', 'd', 'w', 'W', 'c', 'z', 'x', 'v', 'g']
JUNG = ['k', 'o', 'i', 'O', 'j', 'p', 'u', 'P', 'h', 'hk', 'ho', 'hl', 'y', 'n', 'nj', 'np', 'nl', 'b', 'm', 'ml', 'l']
JONG = ['', 'r', 'R', 'rt', 's', 'sw', 'sg', 'e', 'f', 'fr', 'fa', 'fq', 'ft', 'fx', 'fv', 'fg', 'a', 'q', 'qt', 't', 'T', 'd', 'w', 'c', 'z', 'x', 'v', 'g']
JAMO = {'ㄱ': 'r', 'ㄲ': 'R', 'ㄴ': 's', 'ㄷ': 'e', 'ㄸ': 'E', 'ㄹ': 'f', 'ㅁ': 'a', 'ㅂ': 'q', 'ㅃ': 'Q', 'ㅅ': 't', 'ㅆ': 'T', 'ㅇ': 'd', 'ㅈ': 'w', 'ㅉ': 'W', 'ㅊ': 'c', 'ㅋ': 'z', 'ㅌ': 'x', 'ㅍ': 'v', 'ㅎ': 'g', 'ㅏ': 'k', 'ㅐ': 'o', 'ㅑ': 'i', 'ㅒ': 'O', 'ㅓ': 'j', 'ㅔ': 'p', 'ㅕ': 'u', 'ㅖ': 'P', 'ㅗ': 'h', 'ㅘ': 'hk', 'ㅙ': 'ho', 'ㅚ': 'hl', 'ㅛ': 'y', 'ㅜ': 'n', 'ㅝ': 'nj', 'ㅞ': 'np', 'ㅟ': 'nl', 'ㅠ': 'b', 'ㅡ': 'm', 'ㅢ': 'ml', 'ㅣ': 'l'}

def convert_hangul_to_eng(s):
    res = ''
    for ch in s:
        c = ord(ch)
        if 0xAC00 <= c <= 0xD7A3:
            off = c - 0xAC00
            res += CHO[off // 588] + JUNG[(off % 588) // 28] + JONG[off % 28]
        elif ch in JAMO:
            res += JAMO[ch]
        else:
            res += ch
    return res

# ── 4. 브라우저 팝업 및 스마트 자동 분기 (재고 -> 출고등록 / 미등록 -> 입고등록) ──
def open_quick_scan(serial):
    """바코드 스캔 시 재고 유무를 즉시 판별하여 출고등록 또는 입고등록 화면을 최상단으로 호출"""
    # 한글 입력 상태 대비 영문 강제 치환
    serial = convert_hangul_to_eng(serial).strip().upper()

    if BEEP_ENABLED:
        try:
            winsound.Beep(2400, 100)
        except Exception:
            pass

    import urllib.request
    import urllib.parse
    import json

    # 1) 툴 마스터 바코드(TOOL:..., TOOL-..., tool;...) 처리
    s_norm = serial.replace(";", ":").replace("-", ":").replace("_", ":")
    if s_norm.startswith("TOOL:") or s_norm.startswith("OOL:"):
        if is_inventory_form_active():
            print(f"\n[툴 마스터 바코드] 코드: {serial} -> 입고 폼 내부에서 브랜드/품목을 즉시 자동 선택합니다.")
            return
        else:
            # 대시보드나 외부 프로그램에 있을 때 마스터 바코드를 스캔하면 [입고 등록] 폼을 열고 툴을 즉시 세팅
            target_url = f"{SERVER_URL}/inventory/tool_inventory/inventorybatch/add/?initial_master={urllib.parse.quote(serial)}"
            print(f"\n[툴 마스터 바코드] 코드: {serial} -> [입고 등록] 화면을 호출하여 품목을 즉시 선택합니다!")
            webbrowser.open(target_url, new=2)
            _bring_browser_to_front()
            return

    # 2) 활성 폼 감지: 이미 [입고 등록 추가] 또는 [출고 등록 추가] 작성 화면에 커서가 있다면 새 탭 팝업 차단 (웹 폼 내부 연속 누적)
    if is_inventory_form_active():
        print(f"\n[활성 폼 감지] S/N: {serial} -> 이미 입출고 작성 폼이 활성화되어 있어 웹 폼 내부 연속 누적으로 처리합니다.")
        return

    target_url = None
    try:
        api_url = f"{SERVER_URL}/inventory/barcode-api/lookup/?serial={urllib.parse.quote(serial)}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'BarcodeAgent'})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('found') and data.get('is_stock'):
                # 현재 재고 상태 -> 바로 [출고 등록] 화면으로 직행!
                target_url = f"{SERVER_URL}/inventory/tool_inventory/outboundbatch/add/?serial={urllib.parse.quote(serial)}"
                print(f"\n[재고 감지] S/N: {serial} -> [출고 등록] 화면으로 즉시 연결!")
            else:
                # 미등록 신규 상태 -> 바로 [입고 등록] 화면으로 직행!
                target_url = f"{SERVER_URL}/inventory/tool_inventory/inventorybatch/add/?serial={urllib.parse.quote(serial)}"
                print(f"\n[신규 감지] S/N: {serial} -> [입고 등록] 화면으로 즉시 연결!")
    except Exception as e:
        target_url = f"{SERVER_URL}/inventory/tool_inventory/outboundbatch/add/?serial={urllib.parse.quote(serial)}"
        print(f"\n[오프라인/에러] 기본 출고 화면으로 연결: {target_url} ({e})")

    # 브라우저 실행
    webbrowser.open(target_url, new=2)
    _bring_browser_to_front()

def _bring_browser_to_front():
    # Windows 10/11 포커스 강제 활성화 보조 스레드
    def bring_to_front():
        time.sleep(0.35)
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)

    threading.Thread(target=bring_to_front, daemon=True).start()

# ── 5. 가상 키코드 -> 문자 변환 ──
keyboard_state = (ctypes.c_ubyte * 256)()

def vk_to_char(vk_code, scan_code):
    user32.GetKeyboardState(ctypes.byref(keyboard_state))
    buff = (ctypes.c_wchar * 16)()
    res = user32.ToUnicode(vk_code, scan_code, keyboard_state, buff, 16, 0)
    if res > 0:
        return buff[:res]
    return ""
# ── 6. 훅 콜백 프로시저 ──
_hook_proc_ref = None

def low_level_keyboard_proc(nCode, wParam, lParam):
    if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
        kbd = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk = kbd.vkCode
        scan = kbd.scanCode

        if vk == VK_RETURN:
            serial = collector.process_key("", is_enter=True)
            if serial:
                threading.Thread(target=open_quick_scan, args=(serial,), daemon=True).start()
        else:
            char = vk_to_char(vk, scan)
            if char:
                # 여러 글자(한글 등)가 아닐 때 1글자 처리
                for c in char:
                    collector.process_key(c, is_enter=False)

    return user32.CallNextHookEx(None, nCode, wParam, lParam)

# ── 7. 메인 실행 함수 ──
def run_agent():
    global _hook_proc_ref

    # 중복 실행 방지 (Local 네임스페이스로 일반 권한에서도 안전 작동)
    mutex_name = "Local\\AS_APP_Barcode_Agent_Mutex"
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        print("[!] 이미 바코드 에이전트가 실행 중입니다.")
        sys.exit(0)

    print("=======================================================")
    print(" [AS-APP] 사내 바코드 감지 에이전트 (MQ160W 연동)")
    print("=======================================================")
    print(f" [*] 대상 서버: {SERVER_URL}")
    print(f" [*] 스캔 판별 기준: 타건 간격 {MAX_INTERVAL*1000:.0f}ms 이하 & 최소 {MIN_LENGTH}글자")
    print(f" [*] 설정 파일: {CONFIG_FILE}")
    print(" [*] 백그라운드 상주 감시 중... (바코드를 찍으면 즉시 브라우저가 열립니다)")
    print(" [*] 종료하려면 이 창을 닫거나 Ctrl+C 를 누르십시오.")
    print("=======================================================")

    # 시작 알림음
    try:
        winsound.Beep(1500, 100)
    except Exception:
        pass

    # WH_KEYBOARD_LL은 전역 훅이지만 호출 스레드에서 직접 처리하므로 hMod는 NULL(None)이어야 함
    _hook_proc_ref = HOOKPROC(low_level_keyboard_proc)
    h_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _hook_proc_ref, None, 0)

    if not h_hook:
        err = kernel32.GetLastError()
        print(f"[X] 윈도우 키보드 훅 등록 실패! (Error Code: {err})")
        return

    # Windows 메시지 루프
    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(h_hook)
        print("\n[*] 에이전트가 정상 종료되었습니다.")


if __name__ == "__main__":
    run_agent()
