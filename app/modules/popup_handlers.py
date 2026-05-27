"""
Popup Handlers Module
Handles various popups that may appear during the workflow:
- Priority Window
- Rx In Use
- Renewable Request
- Drug Fill popup
- Critical Warning
"""
import time
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def click_cancel_priority():
    """
    Click Cancel on the Priority window if it appears.
    Window title is dynamic, e.g. "Kelsey Carter's Priority"

    Returns:
        bool: True if priority window was found and cancelled
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        priority_win = window.child_window(title_re=".*Priority.*", control_type="Window")
        if not priority_win.exists(timeout=10):
            return False
        cancel_btn = priority_win.child_window(auto_id="uxCancel", control_type="Button")
        cancel_btn.click_input()
        time.sleep(0.5)
        log_print("[POPUP] Priority window cancelled")
        return True
    except Exception:
        return False


def click_cancel_rxinuse():
    """
    Check for Rx In Use popup and click Cancel.

    Returns:
        bool: True if Rx In Use was found (caller should skip this Rx)
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        rxinuse_win = window.child_window(title_re=".*Rx.*In Use.*", control_type="Window")
        if not rxinuse_win.exists(timeout=config.TIMEOUT_POPUP_CHECK):
            return False
        cancel_btn = rxinuse_win.child_window(title="Cancel", control_type="Button")
        cancel_btn.click_input()
        time.sleep(0.3)
        log_print("[POPUP] Rx In Use — cancelled")
        return True
    except Exception:
        return False


def click_cancel_renew():
    """
    Click Cancel on Renewable Request popup if it appears.

    Returns:
        bool: True if found and dismissed
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        renew_win = window.child_window(title_re=".*Renew.*", control_type="Window")
        if not renew_win.exists(timeout=config.TIMEOUT_POPUP_CHECK):
            return False
        cancel_btn = renew_win.child_window(title="Cancel", control_type="Button")
        cancel_btn.click_input()
        time.sleep(0.3)
        log_print("[POPUP] Renewable Request — cancelled")
        return True
    except Exception:
        return False


def dismiss_drugfill_popup():
    """
    Dismiss Drug Fill popup if it appears (clicks OK or Cancel).

    Returns:
        bool: True if found and dismissed
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        drugfill_win = window.child_window(title_re=".*Drug.*Fill.*", control_type="Window")
        if not drugfill_win.exists(timeout=config.TIMEOUT_POPUP_CHECK):
            return False
        ok_btn = drugfill_win.child_window(title="OK", control_type="Button")
        ok_btn.click_input()
        time.sleep(0.3)
        log_print("[POPUP] Drug Fill popup dismissed")
        return True
    except Exception:
        return False


def handle_critical_warning():
    """
    Handle Critical Warning popup with captcha confirmation.

    Returns:
        bool: True if handled or not present
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        crit_win = window.child_window(title_re=".*Critical.*", control_type="Window")
        if not crit_win.exists(timeout=config.TIMEOUT_POPUP_CHECK):
            return True

        try:
            captcha_label = crit_win.child_window(auto_id="uxConfirmCharacters", control_type="Text")
            captcha_text = captcha_label.window_text().strip()
            captcha_input = crit_win.child_window(auto_id="uxConfirmationCharacters", control_type="Edit")
            captcha_input.set_edit_text(captcha_text)
            time.sleep(0.3)
            log_print(f"[POPUP] Critical Warning captcha: '{captcha_text}'")
        except Exception:
            pass

        try:
            continue_btn = crit_win.child_window(auto_id="uxContinue", control_type="Button")
            continue_btn.click_input()
        except Exception:
            try:
                ok_btn = crit_win.child_window(title="OK", control_type="Button")
                ok_btn.click_input()
            except Exception:
                send_keys("{ENTER}")

        time.sleep(0.5)
        log_print("[POPUP] Critical Warning handled")
        return True

    except Exception:
        return True


def handle_all_popups():
    """
    Attempt to dismiss all known popups that may appear after opening an Rx.
    """
    click_cancel_priority()
    click_cancel_renew()
    dismiss_drugfill_popup()
    handle_critical_warning()
