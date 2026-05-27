"""
Pioneer Dispense Priority Module
Reads current priority, compares with API value, and selects new priority if needed.
"""
import time
import pyperclip
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
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


def check_priority(api_priority):
    """
    Read current priority from UI, compare with API value.
    If mismatched, open priority picker via "..." button, paste and save.

    Args:
        api_priority: Expected priority string from API response

    Returns:
        tuple: (success: bool, is_valid: bool)
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Read current priority from the text field
        priority_field = window.child_window(auto_id="uxPrioritySearch", control_type="Edit")
        priority_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        current_value = priority_field.legacy_properties().get('Value', '')
        log_print(f"Priority in UI: '{current_value}'")
        log_print(f"Priority from API: '{api_priority}'")

        # If already matching, no change needed
        if current_value.strip().lower() == str(api_priority).strip().lower():
            log_print("✓ Priority matches — no change needed")
            return True, True

        log_print(f"Priority mismatch — changing to '{api_priority}'")

        # Click "..." button to open Rx Priority window (auto_id: uxPriorityMore)
        dots_btn = window.child_window(auto_id="uxPriorityMore", control_type="Button")
        dots_btn.click_input()
        time.sleep(0.5)

        # Copy priority text to clipboard and paste with Ctrl+V
        pyperclip.copy(str(api_priority))
        send_keys("^v")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Press Enter twice to confirm selection
        send_keys("{ENTER}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{ENTER}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Click Save button in the "Rx Priority" window (auto_id: uxSave)
        priority_window = _app.window(title="Rx Priority")
        priority_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn = priority_window.child_window(auto_id="uxSave", control_type="Button")
        save_btn.click_input()
        time.sleep(0.5)

        # Validate: re-read priority field after save
        updated_value = priority_field.legacy_properties().get('Value', '')
        is_valid = updated_value.strip().lower() == str(api_priority).strip().lower()
        if is_valid:
            log_print(f"✓ Priority updated: '{updated_value}'")
        else:
            log_print(f"✗ Priority update failed: got '{updated_value}', expected '{api_priority}'")

        return True, is_valid

    except Exception as e:
        log_print(f"Failed to check/set priority: {e}")
        return False, False


if __name__ == "__main__":
    success, is_valid = check_priority("Fertility")
    if success and is_valid:
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
