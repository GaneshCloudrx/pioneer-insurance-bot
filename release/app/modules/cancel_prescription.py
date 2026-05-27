"""
Cancel Prescription Module
Clicks Cancel on the Edit Rx window and dismisses the Save Rx? popup by clicking No.
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from pywinauto import Desktop


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer via the main Fill Requests process."""
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
        _app = None
        return False



def click_cancel():
    """
    Click the Cancel (ESC) button on the Edit Rx window,
    then click No on the Save Rx? confirmation popup.

    Returns:
        bool: True if cancelled successfully, False otherwise
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        # Screen Selector: Edit Rx window
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)

        # Target Selector: Cancel - ESC button (found_index=0 picks the Edit Rx one)
        cancel_btn = edit_rx_window.child_window(
            auto_id="uxCancel",
            title="Cancel - ESC",
            control_type="Button",
            found_index=0
        )
        cancel_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        cancel_btn.click_input()
        log_print("✓ Cancel button clicked")

        time.sleep(0.5)

        # Handle Save Rx? popup — it's a child of the Edit Rx window, not a top-level window
        try:
            save_dialog = edit_rx_window.child_window(
                title="Save Rx?",
                control_type="Window"
            )
            save_dialog.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
            no_btn = save_dialog.child_window(title="No", control_type="Button")
            no_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
            no_btn.click_input()
            log_print("✓ Save Rx? popup dismissed (No)")
        except Exception:
            log_print("No Save Rx? popup appeared")

        return True

    except Exception as e:
        log_print(f"Failed to cancel prescription: {e}")
        _app = None
        return False

if __name__ == "__main__":
    if click_cancel():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")