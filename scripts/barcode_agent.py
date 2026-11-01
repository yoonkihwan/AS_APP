"""
=============================================================================
바코드 스캐너 백그라운드 감지 에이전트 (Barcode Background Agent)
=============================================================================
- 모델: MQ160W 미라클 스캐너 (또는 모든 표준 USB HID 바코드 스캐너)
- 환경: Windows 10 / 11 (무창 백그라운드 상주 & 시작프로그램 자동 등록)
- 동작:
    1. 최초 실행 시 윈도우 시작프로그램(HKCU Run 레지스트리)에 자동 등록 (.bat 불필요)
    2. 검은 콘솔 창 없이 100% 백그라운드에서 키보드 스트림(65ms 이하) 감시
    3. 이미 실행 중일 때 다시 더블클릭하면 상태 확인 및 종료 여부 선택 가능
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
import subprocess

# 무창(--noconsole / --windowed) 빌드 시 stdout/stderr None 방어
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

try:
    if hasattr(sys.stdout, "encoding") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── 1. 기본 설정 (agent_config.ini 자동 로드/생성) ──
DEFAULT_CONFIG = {
    "SERVER_URL": "https://cheng-1.com",
    "MAX_KEY_INTERVAL_SEC": "0.065",   # 65ms 이하를 바코드 입력으로 판정
    "MIN_SERIAL_LENGTH": "4",          # 최소 4자리 이상
    "BEEP_ON_SCAN": "True",            # 스캔 성공 시 비프음
}

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "agent_config.ini")

def load_or_create_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        for enc in ("utf-8-sig", "utf-8", "cp949"):
            try:
                config.read(CONFIG_FILE, encoding=enc)
                break
            except Exception:
                continue
    if "SETTINGS" not in config:
        config["SETTINGS"] = DEFAULT_CONFIG
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception:
            pass
    return config["SETTINGS"]

CONFIG = load_or_create_config()
SERVER_URL = CONFIG.get("SERVER_URL", "https://cheng-1.com").rstrip("/")
MAX_INTERVAL = float(CONFIG.get("MAX_KEY_INTERVAL_SEC", "0.065"))
MIN_LENGTH = int(CONFIG.get("MIN_SERIAL_LENGTH", "4"))
BEEP_ENABLED = CONFIG.get("BEEP_ON_SCAN", "True").lower() == "true"

# ── 2. Win32 API 및 레지스트리 자동 등록 ──
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_QUIT = 0x0012
VK_RETURN = 0x0D

MB_OK = 0x00000000
MB_YESNO = 0x00000004
MB_ICONINFORMATION = 0x00000040
MB_ICONQUESTION = 0x00000020
MB_TOPMOST = 0x00040000
IDYES = 6

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


def register_windows_startup():
    """EXE 실행 시 윈도우 시작프로그램(HKCU Run 레지스트리)에 자기 자신을 자동 등록"""
    if not getattr(sys, "frozen", False):
        return False
    try:
        import winreg
        exe_path = os.path.abspath(sys.executable)
        cmd = f'"{exe_path}" --startup'
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "AS_Barcode_Agent", 0, winreg.REG_SZ, cmd)
        return True
    except Exception:
        return False


def unregister_windows_startup():
    """사용자가 에이전트를 수동 종료할 때 시작프로그램 등록 해제 여부 선택 가능"""
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, "AS_Barcode_Agent")
    except Exception:
        pass


# ── 3. 바코드 버퍼 및 판별 로직 ──
class BarcodeCollector:
    def __init__(self):
        self.buffer = []
        self.last_time = 0.0
        self.intervals = []

    def process_key(self, char, is_enter=False):
        now = time.perf_counter()

        if is_enter:
            if len(self.buffer) >= MIN_LENGTH:
                max_gap = max(self.intervals) if self.intervals else 0.0
                if max_gap <= MAX_INTERVAL:
                    serial = "".join(self.buffer).strip()
                    self.reset()
                    return serial
            self.reset()
            return None

        if not self.buffer:
            self.buffer.append(char)
            self.last_time = now
            self.intervals = []
        else:
            interval = now - self.last_time
            self.last_time = now
            if interval <= MAX_INTERVAL:
                self.buffer.append(char)
                self.intervals.append(interval)
            else:
                self.buffer = [char]
                self.intervals = []

        return None

    def reset(self):
        self.buffer = []
        self.intervals = []
        self.last_time = 0.0

collector = BarcodeCollector()


def is_inventory_web_active():
    """현재 최상단 활성 창이 이미 웹 브라우저의 입출고 등록 또는 대시보드 화면인지 검사"""
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
        # 입고 등록, 출고 등록, 또는 장비/툴 관리 대시보드 화면이 이미 최상단에 떠 있으면
        # 웹 페이지 내부의 JS 리스너가 직접 처리하므로 새 탭 팝업을 띄우지 않음!
        active_keywords = ["입고 등록", "출고 등록", "대시보드 | 장비/툴 관리", "inventorybatch/add", "outboundbatch/add"]
        return any(kw in title for kw in active_keywords)
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


# ── 4. 브라우저 팝업 및 스마트 자동 분기 ──
def open_quick_scan(serial):
    serial = convert_hangul_to_eng(serial).strip().upper()

    # 이미 브라우저에서 입고 등록 / 출고 등록 / 대시보드 창이 활성화되어 있다면 웹 JS가 전담 처리
    if is_inventory_web_active():
        return

    if BEEP_ENABLED:
        try:
            winsound.Beep(2400, 100)
        except Exception:
            pass

    import urllib.request
    import urllib.parse
    import json

    # 1) 품목 마스터 바코드(TOOL-...) 처리
    s_norm = serial.replace(";", ":").replace("-", ":").replace("_", ":")
    if s_norm.startswith("TOOL:") or s_norm.startswith("OOL:"):
        target_url = f"{SERVER_URL}/inventory/tool_inventory/inventorybatch/add/?initial_master={urllib.parse.quote(serial)}"
        webbrowser.open(target_url, new=2)
        _bring_browser_to_front()
        return

    # 2) 일반 시리얼 및 박스 품목명 바코드 조회
    target_url = None
    try:
        api_url = f"{SERVER_URL}/inventory/barcode-api/lookup/?serial={urllib.parse.quote(serial)}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'BarcodeAgent'})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('is_tool_model') and data.get('brand_id') and data.get('tool_id'):
                # 박스의 품목명(모델명) 바코드가 찍힌 경우 시리얼로 넣지 않고 해당 품목 선택으로 연결
                master_code = f"TOOL-{data['brand_id']}-{data['tool_id']}"
                target_url = f"{SERVER_URL}/inventory/tool_inventory/inventorybatch/add/?initial_master={urllib.parse.quote(master_code)}"
            elif data.get('found') and data.get('is_stock'):
                target_url = f"{SERVER_URL}/inventory/tool_inventory/outboundbatch/add/?serial={urllib.parse.quote(serial)}"
            else:
                target_url = f"{SERVER_URL}/inventory/tool_inventory/inventorybatch/add/?serial={urllib.parse.quote(serial)}"
    except Exception:
        target_url = f"{SERVER_URL}/inventory/tool_inventory/outboundbatch/add/?serial={urllib.parse.quote(serial)}"

    webbrowser.open(target_url, new=2)
    _bring_browser_to_front()


def _bring_browser_to_front():
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
                for c in char:
                    collector.process_key(c, is_enter=False)

    return user32.CallNextHookEx(None, nCode, wParam, lParam)


# ── 7. 메인 실행 함수 (무창 백그라운드 & 중복 실행 시 종료 제어) ──
def run_agent():
    global _hook_proc_ref

    is_startup_boot = "--startup" in sys.argv

    # 중복 실행 감지 Mutex
    mutex_name = "Local\\AS_APP_Barcode_Agent_Mutex"
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        if not is_startup_boot:
            ans = user32.MessageBoxW(
                None,
                f"현재 바코드 에이전트가 백그라운드에서 정상 실행 중입니다.\n"
                f"• 접속 서버: {SERVER_URL}\n\n"
                f"백그라운드 에이전트를 종료하시겠습니까?\n"
                f"[예(Y): 에이전트 종료] / [아니오(N): 계속 실행 유지]",
                "AS-APP 바코드 에이전트 상태 확인",
                MB_YESNO | MB_ICONQUESTION | MB_TOPMOST,
            )
            if ans == IDYES:
                my_pid = os.getpid()
                subprocess.run(
                    f'taskkill /F /FI "PID ne {my_pid}" /IM barcode_agent.exe',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                user32.MessageBoxW(
                    None,
                    "바코드 에이전트가 종료되었습니다.\n다시 시작하려면 barcode_agent.exe를 실행하십시오.",
                    "AS-APP 바코드 에이전트",
                    MB_OK | MB_ICONINFORMATION | MB_TOPMOST,
                )
        sys.exit(0)

    # 최초 실행 시 윈도우 시작프로그램(레지스트리)에 자동 등록
    register_windows_startup()

    # 시작 알림음
    try:
        winsound.Beep(1500, 100)
    except Exception:
        pass

    # 수동 더블클릭 실행 시 안내 팝업 (부팅 자동 실행 시에는 띄우지 않음)
    if not is_startup_boot and getattr(sys, "frozen", False):
        def show_start_notice():
            user32.MessageBoxW(
                None,
                f"바코드 에이전트가 백그라운드에서 시작되었습니다.\n"
                f"(윈도우 시작프로그램 자동 등록 완료)\n\n"
                f"• 접속 서버: {SERVER_URL}\n"
                f"• 이제 화면에 창이 떠 있지 않아도 바코드 스캔 시 즉시 작동합니다.\n"
                f"• 상태 확인 또는 종료를 원하시면 barcode_agent.exe를 다시 실행하십시오.",
                "AS-APP 바코드 에이전트 실행 완료",
                MB_OK | MB_ICONINFORMATION | MB_TOPMOST,
            )
        threading.Thread(target=show_start_notice, daemon=True).start()

    _hook_proc_ref = HOOKPROC(low_level_keyboard_proc)
    h_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _hook_proc_ref, None, 0)

    if not h_hook:
        sys.exit(1)

    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(h_hook)


if __name__ == "__main__":
    run_agent()
