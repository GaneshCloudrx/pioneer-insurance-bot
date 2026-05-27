"""
Save and Continue Module
Clicks Save & Continue button on the Edit Rx window.
For MDR: uses Ctrl+F12 to Save Only (without Continue).
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
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


def click_save_and_continue():
    """
    Click the Save & Continue button (auto_id: uxSave) on the Edit Rx window.

    Returns:
        bool: True if clicked successfully, False otherwise
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        save_btn = window.child_window(
            auto_id="uxSave",
            title="Save & Continue - F12",
            control_type="Button"
        )
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("✓ Save & Continue clicked")
        time.sleep(1)

        return True

    except Exception as e:
        log_print(f"Failed to save and continue: {e}")
        _app = None
        return False


def click_save_only():
    """
    Save Only using Ctrl+F12 shortcut (MDR only).
    IMPORTANT: Do NOT use F12 alone — that triggers Save & Continue.

    Returns:
        bool: True if successful, False otherwise
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
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
        log_print("✓ Save Only (Ctrl+F12) pressed")
        time.sleep(1)

        return True

    except Exception as e:
        log_print(f"Failed to save only: {e}")
        _app = None
        return False


def click_on_hold():
    """
    Put prescription on hold using Ctrl+H shortcut.

    Returns:
        bool: True if successful, False otherwise
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("^h")
        log_print("✓ On Hold (Ctrl+H) pressed")
        time.sleep(1)

        return True

    except Exception as e:
        log_print(f"Failed to put on hold: {e}")
        _app = None
        return False


def click_save_by_config():
    """
    Save using config.SAVE_METHOD: "save_only" or "save_and_continue".
    """
    method = getattr(config, "SAVE_METHOD", "save_and_continue")
    if method == "save_only":
        return click_save_only()
    if method == "save_and_continue":
        return click_save_and_continue()
    log_print(f"Unknown SAVE_METHOD={method!r}, using Save & Continue")
    return click_save_and_continue()


if __name__ == "__main__":
    if click_save_and_continue():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
