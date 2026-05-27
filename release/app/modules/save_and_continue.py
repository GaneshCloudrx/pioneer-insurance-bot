"""
Save and Continue Module
Clicks Save & Continue button on the Edit Rx window.
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


if __name__ == "__main__":
    if click_save_and_continue():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
