"""
Error and Warning Module
Handles the Error/Warning List window that may appear after Save & Continue.
Returns (passed, non_bypassable) so the caller can decide next steps.
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer."""
    global _app
    try:
        if _app is None:
            _app = Application(backend="uia").connect(
                title_re=config.SELECTOR_EDIT_RX_FULL,
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def handle_error_warning():
    """
    If the Error Warning List window appeared:
      1. Click Save & Continue (uxContinue) on it.
      2. If "Outstanding Errors" (non-bypassable) popup appears -> click OK, cancel warning, return failure.
      3. Otherwise warnings were bypassable -> return success.

    If the window never appeared, that's fine -> return success.

    Returns:
        tuple: (success: bool, non_bypassable: bool)
               success=True  -> saved OK (or no warning window at all)
               success=False, non_bypassable=True -> had non-bypassable errors
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)

        # Check if Error Warning List window exists
        try:
            warning_win = window.child_window(title="Error  Warning List", control_type="Window")
            warning_win.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            return True, False

        log_print("[WARNING] Error Warning List window detected")

        # Step 1: Click Save & Continue on warning window (auto_id: uxContinue)
        save_btn = warning_win.child_window(auto_id="uxContinue", control_type="Button")
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("✓ Warning Save & Continue clicked")
        time.sleep(0.5)

        # Step 2: Check for Outstanding Errors (non-bypassable)
        try:
            outstanding = warning_win.child_window(title="Outstanding Errors", control_type="Window")
            outstanding.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            log_print("✓ Warnings bypassed successfully")
            return True, False

        log_print("[WARNING] Non-bypassable Outstanding Errors detected")
        ok_btn = outstanding.child_window(title="OK", control_type="Button")
        ok_btn.click_input()
        time.sleep(0.3)

        # Cancel the warning window (auto_id: uxClose)
        cancel_btn = warning_win.child_window(auto_id="uxClose", control_type="Button")
        cancel_btn.click_input()
        log_print("✓ Warning window cancelled")

        return False, True

    except Exception as e:
        log_print(f"Error handling warning window: {e}")
        _app = None
        return False, False


def handle_alerts_popup():
    """
    Handle the optional Alerts popup that may appear after saving.
    Clicks Save & Continue (uxSaveContinue) if the window is found.
    Returns True always (popup is optional).
    """
    try:
        time.sleep(1)
        app = Application(backend="uia").connect(title_re=".*Alerts.*", timeout=config.TIMEOUT_POPUP_CHECK)
        alerts_win = app.window(title_re=".*Alerts -.*")
        alerts_win.wait("visible", timeout=config.TIMEOUT_POPUP_CHECK)
        save_btn = alerts_win.child_window(auto_id="uxSaveContinue", control_type="Button")
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("✓ Alerts popup — Save & Continue clicked")
        time.sleep(0.5)
    except Exception:
        pass
    return True


if __name__ == "__main__":
    success = handle_alerts_popup()
    if success:
        log_print("\n✓ TEST PASSED")
    else:
        log_print(f"\n✗ TEST FAILED")
