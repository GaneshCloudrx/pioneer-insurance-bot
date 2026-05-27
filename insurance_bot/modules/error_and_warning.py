"""
Error and Warning Module for Insurance Bot
Handles the Error/Warning List and Alerts popups that appear after Save & Continue.
Same pattern as the DE bot.
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def handle_error_warning():
    """
    Handle the Error Warning List window if it appeared after save:
      1. Click Save & Continue (uxContinue) on it.
      2. If "Outstanding Errors" (non-bypassable) popup appears -> click OK, cancel.
      3. Otherwise warnings were bypassable -> return success.

    Returns:
        tuple: (success: bool, non_bypassable: bool)
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)

        try:
            warning_win = window.child_window(title="Error  Warning List", control_type="Window")
            warning_win.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            return True, False

        log_print("[WARNING] Error Warning List window detected")

        save_btn = warning_win.child_window(auto_id="uxContinue", control_type="Button")
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("[WARNING] Save & Continue clicked on warning window")
        time.sleep(0.5)

        try:
            outstanding = warning_win.child_window(title="Outstanding Errors", control_type="Window")
            outstanding.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            log_print("[WARNING] Warnings bypassed successfully")
            return True, False

        log_print("[WARNING] Non-bypassable Outstanding Errors detected")
        ok_btn = outstanding.child_window(title="OK", control_type="Button")
        ok_btn.click_input()
        time.sleep(0.3)

        cancel_btn = warning_win.child_window(auto_id="uxClose", control_type="Button")
        cancel_btn.click_input()
        log_print("[WARNING] Warning window cancelled")

        return False, True

    except Exception as e:
        log_print(f"[WARNING] Error handling warning window: {e}")
        return False, False


def handle_alerts_popup():
    """
    Handle the optional Alerts popup that may appear after saving.
    Clicks Save & Continue (uxSaveContinue) if the window is found.
    Handles captcha confirmation characters if present.

    Returns:
        bool: True always (popup is optional)
    """
    try:
        app = Application(backend="uia").connect(
            title_re=".*Alerts.*", timeout=config.TIMEOUT_POPUP_CHECK
        )
        alerts_win = app.window(title_re=".*Alerts -.*")
        alerts_win.wait("visible", timeout=config.TIMEOUT_POPUP_CHECK)

        # Handle captcha if present
        try:
            captcha_label = alerts_win.child_window(auto_id="uxConfirmCharacters", control_type="Text")
            if captcha_label.exists(timeout=1):
                captcha_text = captcha_label.window_text().strip()
                captcha_input = alerts_win.child_window(auto_id="uxConfirmationCharacters", control_type="Edit")
                captcha_input.set_edit_text(captcha_text)
                time.sleep(0.3)
                log_print(f"[ALERTS] Captcha filled: '{captcha_text}'")
        except Exception:
            pass

        save_btn = alerts_win.child_window(auto_id="uxSaveContinue", control_type="Button")
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("[ALERTS] Save & Continue clicked")
        time.sleep(0.5)
    except Exception:
        pass
    return True


def handle_equivalent_rx():
    """
    Handle Equivalent Rx with Days Supply popup — click Fill Anyway.

    Returns:
        bool: True if handled or not present
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        fill_btn = window.child_window(auto_id="uxFillAnyway", control_type="Button")
        if not fill_btn.exists(timeout=0):
            return True
        fill_btn.click_input()
        time.sleep(0.3)
        log_print("[POPUP] Equivalent Rx — clicked Fill Anyway")
        return True
    except Exception:
        return True


def handle_equivalent_pending():
    """
    Handle Equivalent Pending Rx popup — click Ignore and Continue.

    Returns:
        bool: True if handled or not present
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        ignore_btn = window.child_window(auto_id="uxIgnoreRenewPending", control_type="Button")
        if not ignore_btn.exists(timeout=2):
            return True
        ignore_btn.click_input()
        time.sleep(0.3)
        log_print("[POPUP] Equivalent Pending Rx — clicked Ignore and Continue")
        return True
    except Exception:
        return True


if __name__ == "__main__":
    success, non_bypassable = handle_error_warning()
    log_print(f"Result: success={success}, non_bypassable={non_bypassable}")
