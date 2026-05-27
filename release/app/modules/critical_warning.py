"""
Critical Warning Module
Handles the critical warning captcha that may appear after Save & Continue.
Reads the 2-char captcha text, types it into the textbox, and clicks Save.
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


def handle_critical_warning():
    """
    If the critical warning captcha window appeared:
      1. Read the 2-char captcha from uxConfirmCharacters label.
      2. Type it into the uxConfirmationCharacters textbox.
      3. Click Save (uxSave).

    If the window did not appear, return success silently.

    Returns:
        bool: True if handled or not present, False on failure
    """
    global _app

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)

        try:
            captcha_win = window.child_window(
                title="Add an Escript Alias for this Patient",
                control_type="Window"
            )
            captcha_win.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            log_print("No critical warning captcha window detected")
            return True

        log_print("[CRITICAL WARNING] Captcha window detected")

        # Read captcha text from the label
        captcha_label = captcha_win.child_window(
            auto_id="uxConfirmCharacters",
            control_type="Text"
        )
        captcha_text = captcha_label.window_text().strip()
        log_print(f"[CRITICAL WARNING] Captcha text: '{captcha_text}'")

        # Type captcha into the textbox
        captcha_input = captcha_win.child_window(
            auto_id="uxConfirmationCharacters",
            control_type="Edit"
        )
        captcha_input.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        captcha_input.set_edit_text(captcha_text)
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Click Save button
        save_btn = captcha_win.child_window(
            auto_id="uxSave",
            control_type="Button"
        )
        save_btn.click_input()
        log_print("✓ Critical warning captcha solved and saved")
        time.sleep(0.5)

        return True

    except Exception as e:
        log_print(f"Failed to handle critical warning: {e}")
        _app = None
        return False


if __name__ == "__main__":
    if handle_critical_warning():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")