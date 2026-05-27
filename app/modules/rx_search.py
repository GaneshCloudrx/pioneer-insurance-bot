"""
Rx Search Module
Searches for a prescription by Rx number in Pioneer's Rx Profile Quick Search,
selects the result, and opens the Edit Rx screen via the Edit button.

Flow:
1. Type Rx number in Quick Search (uxPatientQuickSearch) on Rx Profile window
2. Press Enter to search
3. Press Enter to select the result
4. Click Edit - F4 (uxEdit) to open Edit Rx
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


_app = None


def _connect_to_rx_profile():
    """Connect to Pioneer's Rx Profile window."""
    global _app
    try:
        _app = Application(backend="uia").connect(
            title_re=config.SELECTOR_RX_PROFILE,
            timeout=config.TIMEOUT_ELEMENT_VISIBLE,
        )
        return True
    except Exception as e:
        log_print(f"[RX SEARCH] Failed to connect to Rx Profile: {e}")
        return False


def search_and_open_rx(rx_number):
    """
    Full workflow: type Rx number in Quick Search, select result, click Edit.

    Args:
        rx_number: The prescription Rx number to search for

    Returns:
        tuple: (success: bool, found: bool)
    """
    global _app

    if not _connect_to_rx_profile():
        return False, False

    try:
        window = _app.window(title_re=config.SELECTOR_RX_PROFILE)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Step 1: Type Rx number in Quick Search field
        quick_search = window.child_window(auto_id="uxPatientQuickSearch", control_type="Edit")
        quick_search.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        quick_search.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("^a")
        time.sleep(0.1)
        send_keys("{BACKSPACE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        send_keys(str(rx_number), with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        log_print(f"[RX SEARCH] Typed Rx number: {rx_number}")

        # Step 2: Press Enter to search
        send_keys("{ENTER}")
        time.sleep(config.TIMEOUT_AFTER_SEARCH)
        log_print("[RX SEARCH] Enter pressed — searching")

        # Step 3: Press Enter to select the result
        send_keys("{ENTER}")
        time.sleep(1)
        log_print("[RX SEARCH] Pressed Enter to select result")

        # Step 4: Click Edit - F4 button
        edit_btn = window.child_window(auto_id="uxEdit", control_type="Button")
        edit_btn.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_btn.click_input()
        time.sleep(1)
        log_print("[RX SEARCH] Edit - F4 clicked — opening Edit Rx")

        log_print(f"[RX SEARCH] Rx {rx_number} opened in Edit Rx")
        return True, True

    except Exception as e:
        log_print(f"[RX SEARCH] Failed to search/open Rx: {e}")
        return False, False


if __name__ == "__main__":
    success, found = search_and_open_rx("12345678")
    if success and found:
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
