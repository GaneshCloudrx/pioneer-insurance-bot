"""
Cancel Prescription Module for Insurance Bot
Clicks Cancel on the Edit Rx window and dismisses the Save Rx? popup.
"""
import time
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app, reset


def click_cancel():
    """
    Click the Cancel (ESC) button on the Edit Rx window,
    then click No on the Save Rx? confirmation popup.

    Returns:
        bool: True if cancelled successfully
    """
    try:
        app = get_pioneer_app()
        edit_rx_window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)

        cancel_btn = edit_rx_window.child_window(
            auto_id="uxCancel",
            title="Cancel - ESC",
            control_type="Button",
            found_index=0
        )
        cancel_btn.click_input()
        log_print("[CANCEL] Cancel button clicked")
        time.sleep(0.5)

        # Handle Save Rx? popup
        try:
            save_dialog = edit_rx_window.child_window(
                title="Save Rx?", control_type="Window"
            )
            save_dialog.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
            no_btn = save_dialog.child_window(title="No", control_type="Button")
            no_btn.click_input()
            log_print("[CANCEL] Save Rx? dismissed (No)")
        except Exception:
            pass

        reset()
        return True

    except Exception as e:
        log_print(f"[CANCEL] Failed to cancel: {e}")
        reset()
        return False


if __name__ == "__main__":
    if click_cancel():
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
