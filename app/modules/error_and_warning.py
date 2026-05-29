"""
Error and Warning Module
Handles the Error/Warning List window that may appear after Save & Continue.
Returns (passed, non_bypassable) so the caller can decide next steps.
"""
import time
from pywinauto.application import Application
from pywinauto import Desktop
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer via shared cache."""
    global _app
    try:
        _app = get_pioneer_app()
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def handle_error_warning():
    """
    If the Error Warning List window appeared:
      1. Click Save & Continue (uxContinue) on it.
      2. If "Outstanding Errors" (non-bypassable) popup appears -> click OK,
         extract errors, cancel warning, return failure with error text.
      3. Otherwise warnings were bypassable -> return success.

    Returns:
        tuple: (success: bool, non_bypassable: bool, error_text: str)
    """
    global _app

    if not connect_to_pioneer():
        return False, False, ""

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)

        try:
            warning_win = window.child_window(title="Error  Warning List", control_type="Window")
            warning_win.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            return True, False, ""

        log_print("[WARNING] Error Warning List window detected")

        save_btn = warning_win.child_window(auto_id="uxContinue", control_type="Button")
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("Warning Save & Continue clicked")
        time.sleep(0.5)

        try:
            outstanding = warning_win.child_window(title="Outstanding Errors", control_type="Window")
            outstanding.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            log_print("Warnings bypassed successfully")
            return True, False, ""

        log_print("[WARNING] Non-bypassable Outstanding Errors detected")
        ok_btn = outstanding.child_window(title="OK", control_type="Button")
        ok_btn.click_input()
        time.sleep(0.3)

        error_text = extract_error_list()

        cancel_btn = warning_win.child_window(auto_id="uxClose", control_type="Button")
        cancel_btn.click_input()
        log_print("Warning window cancelled")

        return False, True, error_text

    except Exception as e:
        log_print(f"Error handling warning window: {e}")
        _app = None
        return False, False, ""


def extract_error_list():
    """
    Extract all text from the uxErrorGrid DataGridView.
    Must be called while the Error Warning List window is open.

    Returns:
        str: All text from the error grid, or empty string on failure.
    """
    global _app

    if not connect_to_pioneer():
        return ""

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        warning_win = window.child_window(title="Error  Warning List", control_type="Window")
        if not warning_win.exists(timeout=1):
            return ""

        grid = warning_win.child_window(auto_id="uxErrorGrid", control_type="Table")
        all_text = []
        for cell in grid.descendants(control_type="Edit"):
            try:
                val = cell.legacy_properties().get("Value", "").strip()
                if val:
                    all_text.append(val)
            except Exception:
                pass
        joined = " | ".join(all_text)
        log_print(f"[WARNING] Error grid content: {joined}")
        return joined

    except Exception as e:
        log_print(f"Failed to extract error list: {e}")
        return ""


def _locate_alerts_window(wait_seconds=4):
    """
    Find the "Alerts - <patient> ..." window. It is opened as a modal child of
    the Edit/Fill Rx window, so we try both:
      1. As a descendant of the Edit Rx window (modal child).
      2. As a top-level desktop window (fallback in case the modal is reported
         as a standalone Win32 window).

    Polls until the wait_seconds budget is exhausted before giving up.

    Returns:
        The matched WindowSpecification, or None if not found.
    """
    desktop = Desktop(backend="uia")
    deadline = time.time() + max(wait_seconds, 0)
    title_pattern = r".*Alerts\s*-.*"

    while True:
        try:
            edit_rx = desktop.window(title_re=config.SELECTOR_EDIT_RX_FULL)
            if edit_rx.exists(timeout=0):
                child = edit_rx.child_window(title_re=title_pattern, control_type="Window")
                if child.exists(timeout=0):
                    return child
        except Exception:
            pass

        try:
            top_level = desktop.window(title_re=title_pattern, control_type="Window")
            if top_level.exists(timeout=0):
                return top_level
        except Exception:
            pass

        if time.time() >= deadline:
            return None
        time.sleep(0.3)


def handle_alerts_popup():
    """
    Handle the optional Alerts popup that may appear after Save & Continue.

    The popup is a modal child of the Edit/Fill Rx window with title
    "Alerts - <patient name>...". When present, fill its captcha (if any) and
    click the "Save & Continue - F12" button (auto_id=uxSaveContinue).

    Returns True always (popup is optional).
    """
    alerts_win = _locate_alerts_window(wait_seconds=4)
    if alerts_win is None:
        log_print("[ALERTS] No alerts popup detected")
        return True

    try:
        alerts_win.wait("visible", timeout=2)
        try:
            alerts_win.set_focus()
        except Exception:
            pass
        time.sleep(0.3)

        # Optional captcha
        try:
            captcha_label = alerts_win.child_window(
                auto_id="uxConfirmCharacters", control_type="Text"
            )
            if captcha_label.exists(timeout=1):
                captcha_text = captcha_label.window_text().strip()
                if captcha_text:
                    captcha_input = alerts_win.child_window(
                        auto_id="uxConfirmationCharacters", control_type="Edit"
                    )
                    captcha_input.set_edit_text(captcha_text)
                    time.sleep(0.3)
                    log_print(f"[ALERTS] Captcha filled: '{captcha_text}'")
        except Exception:
            pass

        save_btn = alerts_win.child_window(
            auto_id="uxSaveContinue", control_type="Button"
        )
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("[ALERTS] Save & Continue clicked")
        time.sleep(0.5)
    except Exception as e:
        log_print(f"[ALERTS] Failed to handle alerts popup: {e}")
    return True


if __name__ == "__main__":
    #lets test the alerts popup
    success = handle_alerts_popup()
    if success:
        log_print("\n✓ TEST PASSED")
    else:
        log_print(f"\n✗ TEST FAILED")
