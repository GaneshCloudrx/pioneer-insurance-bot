"""
Pioneer Login Module for Insurance Bot
Reuses the same login pattern as the DE bot.
"""
import time
import os
from datetime import datetime
import psutil
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from pywinauto import mouse
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print

_app = None


def kill_pioneer():
    """Kill any running Pioneer and NewTechBootStrapper processes."""
    TARGET_NAMES = ("PioneerPharmacy", "NewTechBootStrapper")
    try:
        killed = False
        for proc in psutil.process_iter(['name', 'pid']):
            name = proc.info['name'] or ""
            if any(t in name for t in TARGET_NAMES):
                log_print(f"Killing {name} (PID: {proc.info['pid']})")
                proc.kill()
                killed = True
        if killed:
            time.sleep(3)
            log_print("Pioneer processes killed")
        return True
    except Exception as e:
        log_print(f"Error killing Pioneer: {e}")
        return False


def open_pioneer(shortcut_path):
    """Open Pioneer application via shortcut."""
    global _app
    try:
        log_print("Opening Pioneer...")
        os.startfile(shortcut_path)

        is_thursday = datetime.now().weekday() == 3
        if is_thursday:
            log_print("Thursday — waiting for possible update...")
            for _ in range(18):
                try:
                    Application(backend="uia").connect(title_re=config.SELECTOR_LOGIN, timeout=5)
                    break
                except Exception:
                    time.sleep(5)

        time.sleep(8)
        max_attempts = 20 if not is_thursday else 36
        for attempt in range(max_attempts):
            try:
                _app = Application(backend="uia").connect(
                    title_re=config.SELECTOR_LOGIN, timeout=15
                )
                log_print("Pioneer opened and connected")
                return True
            except Exception:
                if attempt < max_attempts - 1:
                    time.sleep(5)
        return False
    except Exception as e:
        log_print(f"Failed to open Pioneer: {e}")
        return False


def login_pioneer(shortcut_path, username, password):
    """
    Complete Pioneer login workflow:
    Kill -> Open -> Login -> Navigate to Rx Profile
    """
    global _app
    log_print("=" * 60)
    log_print("Pioneer Login (Insurance Bot)")
    log_print("=" * 60)

    if not kill_pioneer():
        return False
    if not open_pioneer(shortcut_path):
        return False

    try:
        login_window = _app.window(title_re=config.SELECTOR_LOGIN)
        login_window.wait('exists', timeout=config.TIMEOUT_LOGIN_WINDOW)

        username_box = login_window.child_window(auto_id="uxUserName", control_type="Edit")
        username_box.wait('exists', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        username_box.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        username_box.set_edit_text(username)
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        password_box = login_window.child_window(auto_id="uxPassword", control_type="Edit")
        password_box.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        password_box.set_edit_text(password)
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        if config.LOGIN_SERVER:
            server_box = login_window.child_window(auto_id="1001", control_type="Edit")
            server_box.set_focus()
            time.sleep(config.TIMEOUT_AFTER_CLICK)
            send_keys(config.LOGIN_SERVER, with_spaces=True)
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys("{TAB}")
            time.sleep(0.5)

        logon_btn = login_window.child_window(auto_id="uxLogon", control_type="Button")
        logon_btn.click_input()
        time.sleep(3)

        # Dismiss software feedback if it appears
        try:
            feedback_win = _app.window(title_re=".*Software Feedback.*")
            if feedback_win.exists(timeout=2):
                prefer_btn = feedback_win.child_window(title_re=".*Prefer not.*", control_type="Button")
                prefer_btn.click_input()
                time.sleep(0.5)
        except Exception:
            pass

        # Wait for main window
        main_window = _app.window(auto_id="MainForm")
        main_window.wait('visible', timeout=config.TIMEOUT_MAIN_WINDOW)
        main_window.maximize()

        log_print("Login Complete — navigating to Rx Profile")
        return True

    except Exception as e:
        log_print(f"Login failed: {e}")
        return False


def navigate_to_rx_profile():
    """Navigate to Rx Profile tab from main window."""
    global _app
    try:
        main_window = _app.window(auto_id="MainForm")
        side_pane = main_window.child_window(auto_id="uxToDoExplorer", control_type="Pane")
        side_pane.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        mouse.double_click(coords=(1796, 225))
        time.sleep(1)
        log_print("Navigated to Fill Requests / Rx Profile")
        return True
    except Exception as e:
        log_print(f"Failed to navigate: {e}")
        return False


def get_app():
    """Get the current app reference."""
    return _app
