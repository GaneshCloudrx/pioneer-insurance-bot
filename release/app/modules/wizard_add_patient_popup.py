"""
Pioneer Add Patient Condition Wizard Popup Handler
Dismisses the "Add Patient Condition Wizard" popup by clicking Cancel if it appears.
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
                title_re=".*(Fill Requests|Edit|Fill Rx).*",
                timeout=config.TIMEOUT_POPUP_CHECK
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def dismiss_wizard_popup():
    """
    Check if the "Add Patient Condition Wizard" popup is visible.
    If so, click the Cancel button to dismiss it.

    Returns:
        tuple: (success: bool, was_dismissed: bool)
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    try:
        main_window = _app.window(title_re=".*(Fill Requests|Edit|Fill Rx).*")
        main_window.wait('visible', timeout=config.TIMEOUT_POPUP_CHECK)

        wizard_popup = main_window.child_window(title="Add Patient Condition Wizard", control_type="Window")
        if not wizard_popup.exists(timeout=config.TIMEOUT_POPUP_CHECK):
            log_print("No wizard popup found — skipping")
            return True, False

        wizard_popup.wait('visible', timeout=config.TIMEOUT_POPUP_CHECK)
        wizard_popup.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        log_print("Add Patient Condition Wizard popup detected")

        cancel_btn = wizard_popup.child_window(auto_id="uxCancel", control_type="Button")
        cancel_btn.click_input()
        time.sleep(0.5)

        dismissed = not wizard_popup.exists(timeout=2)
        if dismissed:
            log_print("✓ Wizard popup dismissed")
        else:
            log_print("✗ Wizard popup still visible after clicking Cancel")

        return True, dismissed

    except Exception as e:
        log_print(f"Failed to handle wizard popup: {e}")
        return False, False


if __name__ == "__main__":
    success, dismissed = dismiss_wizard_popup()
    if success:
        log_print(f"\n✓ TEST PASSED (dismissed={dismissed})")
    else:
        log_print("\n✗ TEST FAILED")
