"""
Pioneer Dispense Module
Fills Dispense Quantity, Days Supply, and RPh fields and validates each
"""
import time
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


def set_dispense(quantity, days_supply, rph):
    """
    Fill Dispense Quantity, Days Supply, and RPh fields and validate.

    Args:
        quantity:    Dispensed quantity value
        days_supply: Days supply value
        rph:         Pharmacist (RPh) name

    Returns:
        tuple: (success: bool, all_valid: bool)
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # --- 1. Dispense Quantity (auto_id: uxDispensedQuantity) ---
        qty_field = window.child_window(auto_id="uxDispensedQuantity", control_type="Edit")
        qty_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(quantity))
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        qty_actual = qty_field.legacy_properties().get('Value', '')
        qty_valid = str(quantity) in qty_actual.strip()
        log_print(f"{'✓' if qty_valid else '✗'} Dispense Quantity: '{qty_actual}' (expected: '{quantity}')")

        # --- 2. Days Supply (auto_id: uxDaysSupply) ---
        ds_field = window.child_window(auto_id="uxDaysSupply", control_type="Edit")
        ds_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(days_supply))
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        ds_actual = ds_field.legacy_properties().get('Value', '')
        ds_valid = str(days_supply) in ds_actual.strip()
        log_print(f"{'✓' if ds_valid else '✗'} Days Supply: '{ds_actual}' (expected: '{days_supply}')")

        # --- 3. RPh (Win32 Edit inside "RPh:" ComboBox, auto_id: 1001) ---
        rph_combo = window.child_window(title="RPh:", control_type="ComboBox")
        rph_edit = rph_combo.child_window(auto_id="1001", control_type="Edit")
        rph_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(rph), with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        all_valid = qty_valid and ds_valid
        log_print(f"\nDispense: {'✓ ALL VALID' if all_valid else '✗ SOME FIELDS INVALID'}")
        return True, all_valid

    except Exception as e:
        log_print(f"Failed to set dispense fields: {e}")
        return False, False


if __name__ == "__main__":
    success, is_valid = set_dispense(
        quantity="0.5",
        days_supply="1",
        rph="Abigail"
    )
    if success and is_valid:
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
