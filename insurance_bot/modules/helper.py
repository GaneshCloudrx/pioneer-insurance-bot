"""
Helper functions for Pioneer Insurance Bot: logging, screenshots, screen resolution
"""
import os
import csv
import time
import ctypes
import threading
from datetime import datetime
from PIL import ImageGrab
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

log_file = None


def init_log_file():
    """Open (append) a date-stamped log file inside logs/."""
    global log_file
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(config.LOGS_DIR, f"log_{date_str}.txt")
    log_file = open(path, "a", encoding="utf-8")


def close_log_file():
    global log_file
    if log_file:
        log_file.close()
        log_file = None


def log_print(message):
    """Print to console + write to log file."""
    print(message)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_file:
        log_file.write(f"{ts} - {message}\n")
        log_file.flush()


_REPORT_COLS = [
    "Timestamp", "Patient ID", "Patient Name",
    "Rx Number", "Insurance Payer",
    "Status", "Remark",
]


def save_to_report(data, status, remark=""):
    """Append one row to today's daily report CSV."""
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(config.REPORTS_DIR, f"report_{date_str}.csv")
    file_exists = os.path.exists(path) and os.path.getsize(path) > 0
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(_REPORT_COLS)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get("patient_id", ""),
                f"{data.get('first_name', '')} {data.get('last_name', '')}",
                data.get("current_rx", ""),
                data.get("payer", ""),
                status, remark,
            ])
    except Exception as e:
        log_print(f"[REPORT] Failed to write report row: {e}")


def take_screenshot(prefix="screenshot"):
    """Capture the screen and save as PNG."""
    try:
        os.makedirs(config.RECORDINGS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(config.RECORDINGS_DIR, f"{prefix}_{timestamp}.png")
        ImageGrab.grab().save(filepath)
        log_print(f"[SCREENSHOT] Saved: {filepath}")
        return filepath
    except Exception as e:
        log_print(f"[SCREENSHOT] Failed: {e}")
        return None


def get_screen_resolution():
    """Get current screen resolution."""
    try:
        user32 = ctypes.windll.user32
        return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    except Exception:
        return (None, None)


def set_screen_resolution(width=1920, height=1080):
    """Set screen resolution using Windows API."""
    try:
        cur_w, cur_h = get_screen_resolution()
        if cur_w == width and cur_h == height:
            log_print(f"Screen resolution already set to {width} X {height}")
            return True

        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32),
                ("dmSpecVersion", ctypes.c_ushort),
                ("dmDriverVersion", ctypes.c_ushort),
                ("dmSize", ctypes.c_ushort),
                ("dmDriverExtra", ctypes.c_ushort),
                ("dmFields", ctypes.c_ulong),
                ("dmOrientation", ctypes.c_short),
                ("dmPaperSize", ctypes.c_short),
                ("dmPaperLength", ctypes.c_short),
                ("dmPaperWidth", ctypes.c_short),
                ("dmScale", ctypes.c_short),
                ("dmCopies", ctypes.c_short),
                ("dmDefaultSource", ctypes.c_short),
                ("dmPrintQuality", ctypes.c_short),
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", ctypes.c_ushort),
                ("dmBitsPerPel", ctypes.c_ulong),
                ("dmPelsWidth", ctypes.c_ulong),
                ("dmPelsHeight", ctypes.c_ulong),
                ("dmDisplayFlags", ctypes.c_ulong),
                ("dmDisplayFrequency", ctypes.c_ulong),
            ]

        user32 = ctypes.windll.user32
        dm = DEVMODE()
        dm.dmSize = ctypes.sizeof(DEVMODE)
        dm.dmPelsWidth = width
        dm.dmPelsHeight = height
        dm.dmFields = 0x00080000 | 0x00100000

        if user32.ChangeDisplaySettingsW(ctypes.byref(dm), 0x00000002) != 0:
            return False
        if user32.ChangeDisplaySettingsW(ctypes.byref(dm), 0x00000001) == 0:
            time.sleep(0.5)
            log_print(f"Resolution set to {width} X {height}")
            return True
        return False
    except Exception as e:
        log_print(f"Error setting resolution: {e}")
        return False


def ensure_session_active():
    """Reset Windows idle timer."""
    ctypes.windll.kernel32.SetThreadExecutionState(
        0x80000000 | 0x00000001 | 0x00000002
    )


def force_foreground(hwnd):
    """Forcibly bring a window to the foreground."""
    user32 = ctypes.windll.user32
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
