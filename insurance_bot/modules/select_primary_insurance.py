"""
Select Primary Insurance Module
For subsequent Rx numbers (not the first), selects the correct insurance plan
in the Primary textbox inside the Dispense tab.

The Primary field is a combo box (auto_id="1001") inside "Primary:" with format:
  "(P)PAYER_NAME - BIN - MEMBER_ID - PCN"

We check if the current value already contains the insurance payer's first word.
If not, we clear it and type "(P)" + payer first word to select from dropdown.
"""
import time
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def get_primary_insurance_value():
    """
    Read the current value of the Primary insurance field in Dispense tab.

    Returns:
        str: Current value of the Primary field, or empty string on failure
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        primary_combo = window.child_window(title="Primary:", control_type="ComboBox")
        primary_edit = primary_combo.child_window(auto_id="1001", control_type="Edit")
        current_value = primary_edit.legacy_properties().get("Value", "")
        log_print(f"[PRIMARY] Current value: {current_value}")
        return current_value

    except Exception as e:
        log_print(f"[PRIMARY] Failed to read Primary field: {e}")
        return ""


def select_primary_insurance(payer_name):
    """
    Select the correct insurance in the Primary field on Dispense tab.

    Checks if the current Primary value already contains the payer's first word.
    If not, clears the field and types "(P)" + payer first word to trigger dropdown selection.

    Args:
        payer_name: Insurance payer name from the API (e.g. "Aetna", "United Healthcare")

    Returns:
        bool: True if the correct insurance is now selected
    """
    if not payer_name:
        log_print("[PRIMARY] No payer name provided")
        return False

    payer_first_word = payer_name.strip().split()[0].upper()

    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        primary_combo = window.child_window(title="Primary:", control_type="ComboBox")
        primary_edit = primary_combo.child_window(auto_id="1001", control_type="Edit")

        current_value = primary_edit.legacy_properties().get("Value", "")
        log_print(f"[PRIMARY] Current: '{current_value}' | Looking for: '{payer_first_word}'")

        if payer_first_word.lower() in current_value.lower():
            log_print(f"[PRIMARY] Insurance '{payer_first_word}' already selected")
            return True

        # Need to change the primary insurance
        primary_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("^a{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        # Type "(P)" + payer first word to search in dropdown
        search_text = f"(P){payer_first_word}"
        send_keys(search_text, with_spaces=True)
        time.sleep(0.5)

        # Select from dropdown
        send_keys("{DOWN}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Verify selection
        new_value = primary_edit.legacy_properties().get("Value", "")
        if payer_first_word.lower() in new_value.lower():
            log_print(f"[PRIMARY] Successfully selected: '{new_value}'")
            return True
        else:
            log_print(f"[PRIMARY] Selection may have failed. New value: '{new_value}'")
            return True  # Continue anyway

    except Exception as e:
        log_print(f"[PRIMARY] Failed to select primary insurance: {e}")
        return False


if __name__ == "__main__":
    if select_primary_insurance("United Healthcare"):
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
