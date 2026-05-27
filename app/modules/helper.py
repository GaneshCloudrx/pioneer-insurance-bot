"""
Helper functions for Pioneer bot: logging, reporting, screen recording, screen resolution
"""
import os
import csv
import time
import queue
import ctypes
import threading
import subprocess
from datetime import datetime
import requests
from PIL import ImageGrab
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

log_file = None
screen_recorder = None
log_queue_manager = None


# ── Async API Log Queue ─────────────────────────────────────────────────────

class LogQueueManager:
    """Batches log messages and sends them to the API in a background thread."""

    def __init__(self):
        self.queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        os.makedirs(config.LOGS_DIR, exist_ok=True)
        self.last_sent_line_file = os.path.join(config.LOGS_DIR, "last_sent_line.txt")
        self.batch = []
        self.last_batch_time = time.time()

    def start(self):
        if not config.API_LOG_ENABLED:
            return
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        self._send_missed_logs()

    def stop(self):
        if not self.running:
            return
        self.running = False
        try:
            while not self.queue.empty():
                try:
                    self.batch.append(self.queue.get_nowait())
                except queue.Empty:
                    break
        except Exception:
            pass
        if self.batch:
            self._send_batch_to_api()
            self.batch = []
        try:
            if self.worker_thread:
                self.worker_thread.join(timeout=2)
        except Exception:
            pass

    def add_log(self, timestamp, message):
        if not config.API_LOG_ENABLED:
            return
        try:
            self.queue.put_nowait({"timestamp": timestamp, "message": message})
        except queue.Full:
            pass

    def _worker(self):
        while self.running:
            try:
                collected_any = False
                for _ in range(config.API_LOG_BATCH_SIZE):
                    try:
                        self.batch.append(self.queue.get(timeout=0.1))
                        collected_any = True
                    except queue.Empty:
                        break

                should_send = False
                now = time.time()
                if len(self.batch) >= config.API_LOG_BATCH_SIZE:
                    should_send = True
                elif self.batch and (now - self.last_batch_time) >= config.API_LOG_BATCH_INTERVAL:
                    should_send = True

                if should_send:
                    self._send_batch_to_api()
                    self.batch = []
                    self.last_batch_time = now
                elif not collected_any:
                    time.sleep(0.1)
            except Exception as e:
                self._write_error_to_log_file(f"Log queue worker error: {e}")
                time.sleep(1)

    def _send_batch_to_api(self):
        if not self.batch:
            return
        try:
            payload = {
                "bot_name": config.BOT_NAME,
                "server_name": config.MACHINE_NAME,
                "logs": [{"timestamp": l["timestamp"], "message": l["message"]} for l in self.batch],
            }
            resp = requests.post(
                config.API_LOG_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json", "Authorization": config.API_AUTH_HEADER},
                timeout=config.API_TIMEOUT,
            )
            if resp.status_code != 200:
                self._write_error_to_log_file(f"API log send failed {resp.status_code}: {resp.text}")
        except Exception as e:
            self._write_error_to_log_file(f"Failed to send logs to API: {e}")

    def _write_error_to_log_file(self, error_message):
        try:
            if log_file:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{ts} - [LOG QUEUE ERROR] {error_message}\n")
                log_file.flush()
        except Exception:
            pass

    def _send_missed_logs(self):
        if not os.path.exists(self.last_sent_line_file):
            return
        try:
            with open(self.last_sent_line_file, "r") as f:
                last_sent_line = int(f.read().strip())
        except Exception:
            last_sent_line = 0
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_path = os.path.join(config.LOGS_DIR, f"log_{date_str}.txt")
        if not os.path.exists(log_path):
            return
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = lines[last_sent_line:]
            if not new_lines:
                return
            batch = []
            for line in new_lines:
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    batch.append({"timestamp": parts[0].strip(), "message": parts[1].strip()})
            if batch:
                for i in range(0, len(batch), config.API_LOG_BATCH_SIZE):
                    self.batch = batch[i : i + config.API_LOG_BATCH_SIZE]
                    self._send_batch_to_api()
                    self.batch = []
                    time.sleep(0.1)
                with open(self.last_sent_line_file, "w") as f:
                    f.write(str(len(lines)))
        except Exception as e:
            self._write_error_to_log_file(f"Error sending missed logs: {e}")


# ── Local File Logging ───────────────────────────────────────────────────────

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
    """Print to console + write to log file + queue to API."""
    print(message)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_file:
        log_file.write(f"{ts} - {message}\n")
        log_file.flush()
    if log_queue_manager:
        log_queue_manager.add_log(ts, message)


# ── API Log Queue Init / Cleanup ─────────────────────────────────────────────

def init_log_queue_manager():
    global log_queue_manager
    if not config.API_LOG_ENABLED:
        return None
    log_queue_manager = LogQueueManager()
    log_queue_manager.start()
    return log_queue_manager


def close_log_queue_manager():
    global log_queue_manager
    if log_queue_manager:
        log_queue_manager.stop()
        log_queue_manager = None


# ── Daily CSV Report ─────────────────────────────────────────────────────────

_REPORT_COLS = [
    "Timestamp", "Patient ID", "Patient Name",
    "Rx Numbers", "Insurance Payer",
    "Status", "Remark",
]


def save_to_report(tx, status, remark=""):
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
                tx.get("patient_id", ""),
                f"{tx.get('first_name', '')} {tx.get('last_name', '')}".strip(),
                tx.get("current_rx", ""),
                tx.get("payer", ""),
                status, remark,
            ])
    except Exception as e:
        log_print(f"[REPORT] Failed to write report row: {e}")


# ── Screen Recording ─────────────────────────────────────────────────────────

def start_recording():
    """Start session-wide screen recording (auto-rotates at max file size)."""
    global screen_recorder
    try:
        import modules.screen_recorder as sr_module
        screen_recorder = sr_module.ScreenRecorder(
            output_dir=config.RECORDINGS_DIR,
            fps=config.RECORDING_FPS,
            quality=config.RECORDING_QUALITY,
            max_file_size_gb=config.RECORDING_MAX_SIZE_GB,
        )
        screen_recorder.start_recording()
        log_print(f"Screen recording started (auto-rotate at {config.RECORDING_MAX_SIZE_GB}GB)")
        return True
    except Exception as e:
        log_print(f"WARNING: Failed to start screen recording: {e}")
        screen_recorder = None
        return False


def stop_recording():
    """Stop recording and return saved file path."""
    global screen_recorder
    if not screen_recorder:
        return None
    try:
        path = screen_recorder.stop_recording()
        if path:
            log_print(f"Screen recording saved: {path}")
        return path
    except Exception as e:
        log_print(f"Error stopping screen recording: {e}")
        return None
    finally:
        screen_recorder = None


def cleanup_old_recordings(days_old=1):
    """Delete recording files older than *days_old* days."""
    try:
        d = config.RECORDINGS_DIR
        if not os.path.exists(d):
            return
        cutoff = time.time() - (days_old * 86400)
        for fn in os.listdir(d):
            fp = os.path.join(d, fn)
            if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
                os.remove(fp)
                log_print(f"Deleted old recording: {fn}")
    except Exception as e:
        log_print(f"Cleanup error: {e}")


# ── Screen Resolution ────────────────────────────────────────────────────────

def get_screen_resolution():
    """Get current screen resolution using Windows API."""
    try:
        user32 = ctypes.windll.user32
        return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    except Exception:
        return (None, None)


def get_and_log_screen_resolution(context=""):
    """Get screen resolution and log it."""
    width, height = get_screen_resolution()
    if width and height:
        ctx = f" [{context}]" if context else ""
        log_print(f"Screen Resolution{ctx}: {width} X {height}")
    return (width, height)


def set_screen_resolution(width=1920, height=1080):
    """Set screen resolution using Windows API."""
    try:
        cur_w, cur_h = get_screen_resolution()
        if cur_w == width and cur_h == height:
            log_print(f"Screen resolution already set to {width} X {height}")
            return True

        log_print(f"Current resolution: {cur_w} X {cur_h}")
        log_print(f"Setting resolution to {width} X {height}...")

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
        dm.dmFields = 0x00080000 | 0x00100000  # DM_PELSWIDTH | DM_PELSHEIGHT

        if user32.ChangeDisplaySettingsW(ctypes.byref(dm), 0x00000002) != 0:
            log_print(f"Resolution {width} X {height} not supported")
            return False

        if user32.ChangeDisplaySettingsW(ctypes.byref(dm), 0x00000001) == 0:
            time.sleep(0.5)
            new_w, new_h = get_screen_resolution()
            if new_w == width and new_h == height:
                log_print(f"Resolution set to {width} X {height}")
                return True

        log_print("Failed to set resolution")
        return False
    except Exception as e:
        log_print(f"Error setting resolution: {e}")
        return False


# ── Screenshot ───────────────────────────────────────────────────────────────

def take_screenshot(prefix="screenshot"):
    """Capture the screen and save as PNG in the recordings folder."""
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


# ── Session / Focus Helpers ──────────────────────────────────────────────────

def ensure_session_active():
    """Reset Windows idle timer so the session is never marked idle."""
    ctypes.windll.kernel32.SetThreadExecutionState(
        0x80000000 | 0x00000001 | 0x00000002  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )


def is_desktop_locked():
    """Return True if the interactive desktop is not accessible (session locked)."""
    hDesktop = ctypes.windll.user32.OpenInputDesktop(0, False, 0x0001)  # DESKTOP_READOBJECTS
    if hDesktop:
        ctypes.windll.user32.CloseDesktop(hDesktop)
        return False
    return True


def force_foreground(hwnd):
    """Forcibly bring a window to the foreground by its Win32 handle."""
    user32 = ctypes.windll.user32
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)      # SW_RESTORE only if minimized
    user32.SetForegroundWindow(hwnd)


def restart_server(reason="Unrecoverable error", delay_seconds=10):
    """Log the reason and restart the Windows server after a delay."""
    stop_recording()
    log_print(f"[RESTART] Restarting server in {delay_seconds}s — reason: {reason}")
    subprocess.run(["shutdown", "/r", "/t", str(delay_seconds), "/f"], check=True)
