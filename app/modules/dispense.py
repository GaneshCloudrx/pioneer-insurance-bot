"""
Dispense Module
Helpers that interact with the Dispense tab of the Edit Rx window:

- `primary_member_id_matches(member_id)` - read the Primary insurance combo
  on Dispense and return True if the API cardholder digits already appear
  in it. Used by `process_state` to short-circuit a patient when their
  Primary is already configured.
- `clear_secondary_insurance()`          - resolves the "third party setup
  for primary claim submission only" error by setting Secondary to <None>.
- `toggle_daw()`                         - resolves DAW (Dispense As
  Written) errors by flipping the DAW checkbox.

The latter two mirror the equivalents in the CloudRx DE bot so the
save-and-continue recovery loop in `states/process_state.py` can call them.
"""
import time
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
        log_print(f"[DISPENSE] Failed to connect: {e}")
        return False


def _digits_only(value):
    """Return only the numeric digits from `value`."""
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def read_primary_value():
    """
    Read the current value of the Primary insurance combo on the Dispense tab.

    Returns:
        str: The combo's displayed value (e.g.
             "(P)BCBS OF Michigan - 610011 - WYO919752481 - BCBSMAN"),
             or empty string on failure.
    """
    global _app
    _app = None
    if not connect_to_pioneer():
        return ""

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        primary_combo = window.child_window(title="Primary:", control_type="ComboBox")
        primary_edit = primary_combo.child_window(auto_id="1001", control_type="Edit")
        value = primary_edit.legacy_properties().get("Value", "") or ""
        log_print(f"[DISPENSE] Primary value: '{value}'")
        return value
    except Exception as e:
        log_print(f"[DISPENSE] Could not read Primary insurance: {e}")
        return ""


def primary_member_id_matches(member_id):
    """
    Decide whether the Primary insurance combo on the Dispense tab already
    represents the API's insurance for this patient.

    Matching is digits-only: the API cardholder id may carry letter prefixes
    (e.g. "Wyo919752481") and so may the value Pioneer renders in the combo
    ("(P)... - WYO919752481 - ..."). We extract the digits from both sides
    and look for a substring match — if found, the right payer is already
    selected and all Rx numbers for this patient can be skipped.

    Args:
        member_id: Cardholder / member id from the API response.

    Returns:
        bool: True if the cardholder digits already appear in the Primary
              field's displayed value.
    """
    target_digits = _digits_only(member_id)
    if not target_digits:
        log_print("[DISPENSE] No member id digits to match against Primary")
        return False

    current_value = read_primary_value()
    if not current_value:
        return False

    current_digits = _digits_only(current_value)
    if target_digits and target_digits in current_digits:
        log_print(
            f"[DISPENSE] Primary already shows member id '{target_digits}' "
            f"(value='{current_value}')"
        )
        return True

    log_print(
        f"[DISPENSE] Primary does NOT contain member id '{target_digits}' "
        f"(value='{current_value}')"
    )
    return False


def clear_secondary_insurance():
    """Set Secondary insurance to <None> to resolve Third Party errors."""
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        sec_combo = window.child_window(title="Secondary:", control_type="ComboBox")
        sec_edit = sec_combo.child_window(auto_id="1001", control_type="Edit")
        sec_edit.click_input()
        time.sleep(0.2)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(0.2)
        send_keys("<None>", with_spaces=True)
        time.sleep(0.3)
        send_keys("{TAB}")
        time.sleep(0.5)
        log_print("[DISPENSE] Secondary insurance set to <None>")
        return True

    except Exception as e:
        log_print(f"[DISPENSE] Failed to set secondary insurance: {e}")
        return False


def toggle_daw():
    """Toggle the DAW checkbox on the Dispense tab."""
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        daw_checkbox = window.child_window(auto_id="uxDawCode", control_type="CheckBox")
        daw_checkbox.click_input()
        time.sleep(0.3)
        log_print("[DISPENSE] DAW checkbox toggled")
        return True

    except Exception as e:
        log_print(f"[DISPENSE] Failed to toggle DAW: {e}")
        return False


if __name__ == "__main__":
    if toggle_daw():
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
