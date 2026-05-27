"""
Pioneer Equivalent Rx Popup Handler
Clicks 'Fill Anyway' if the Equivalent Rx with Days Supply popup appears
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


_app = None


def click_fill_anyway():
    """
    Click 'Fill Anyway - F2' on the Equivalent Rx popup if it appears.
    
    Returns:
        bool: True if clicked successfully, False if popup not found
    """
    global _app

    try:
        _app = get_pioneer_app()

        eq_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        fill_btn = eq_window.child_window(auto_id="uxFillAnyway", control_type="Button")
        if not fill_btn.exists(timeout=0):
            log_print("Equivalent Rx popup not found")
            return False

        fill_btn.click_input()
        time.sleep(0.3)

        log_print("Equivalent Rx popup — clicked Fill Anyway")
        _app = None
        return True

    except Exception as e:
        log_print(f"Equivalent Rx popup check: {e}")
        return False


def click_ignore_and_continue():
    """
    Click '3 - Ignore and Continue (F4)' on Equivalent Pending Rx Exists popup if it appears.

    Returns:
        bool: True if clicked successfully, False if popup not found
    """
    global _app

    try:
        _app = get_pioneer_app()

        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        ignore_btn = window.child_window(auto_id="uxIgnoreRenewPending", control_type="Button")
        if not ignore_btn.exists(timeout=2):
            log_print("Equivalent Pending Rx popup not found")
            return False

        ignore_btn.click_input()
        time.sleep(0.3)

        log_print("Equivalent Pending Rx popup — clicked Ignore and Continue")
        _app = None
        return True

    except Exception as e:
        log_print(f"Equivalent Pending Rx popup check: {e}")
        return False


if __name__ == "__main__":
    if click_fill_anyway():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
