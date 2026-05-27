"""
Save and Continue Module for Insurance Bot
Clicks Save & Continue (F12) on the Edit Rx window.
"""
import time
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def click_save_and_continue():
    """
    Click the Save & Continue button (auto_id: uxSave) on the Edit Rx window.

    Returns:
        bool: True if clicked successfully
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        save_btn = window.child_window(
            auto_id="uxSave",
            title="Save & Continue - F12",
            control_type="Button"
        )
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("[SAVE] Save & Continue clicked")
        time.sleep(1)
        return True

    except Exception as e:
        log_print(f"[SAVE] Failed to save and continue: {e}")
        return False


def click_save_only():
    """
    Save Only using Ctrl+F12 shortcut.

    Returns:
        bool: True if successful
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        save_btn = window.child_window(
            auto_id="uxSave",
            title="Save & Continue - F12",
            control_type="Button"
        )
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("{VK_CONTROL down}")
        time.sleep(0.5)
        send_keys("{F12}")
        send_keys("{VK_CONTROL up}")
        log_print("[SAVE] Save Only (Ctrl+F12) pressed")
        time.sleep(1)
        return True

    except Exception as e:
        log_print(f"[SAVE] Failed to save only: {e}")
        return False


if __name__ == "__main__":
    if click_save_and_continue():
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
