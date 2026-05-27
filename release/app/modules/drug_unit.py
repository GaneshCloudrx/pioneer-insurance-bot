"""
Pioneer Drug Unit Module
Selects unit (EA/ML/GM) based on transferred_unit value and validates
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


# Global app reference
_app = None

# Unit mapping: transferred_unit value -> display text
UNIT_MAP = {
    "1": "EA",
    "2": "ML",
    "3": "GM",
}
DEFAULT_UNIT = "EA"


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


def set_unit(transferred_unit):
    """
    Select unit based on transferred_unit value and validate.
    
    Args:
        transferred_unit: Value from API (2=ML, 3=GM, default=EA)
    
    Returns:
        tuple: (success: bool, is_valid: bool)
    """
    global _app
    
    if not connect_to_pioneer():
        return False, False
    
    expected_unit = UNIT_MAP.get(str(transferred_unit), DEFAULT_UNIT)
    
    try:
        # Screen Selector: Edit/Fill Rx window
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Unit combo box (fixed auto_id from PA selector)
        unit_combo = edit_rx_window.child_window(auto_id="uxQuantityPrescribedUnit", control_type="ComboBox")
        unit_field = unit_combo.child_window(class_name="Edit")
        unit_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{BACKSPACE}" * 10)
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(expected_unit)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}{ENTER}")
        time.sleep(0.5)
        
        # Validate: read back value
        actual_value = (
            unit_combo.legacy_properties().get('Value', '') or
            unit_field.legacy_properties().get('Value', '')
        )
        log_print(f"Unit set: '{actual_value}' (expected: '{expected_unit}')")
        
        is_valid = expected_unit.lower() in actual_value.strip().lower()
        if is_valid:
            log_print(f"✓ Unit validated: '{actual_value}'")
        else:
            log_print(f"✗ Unit mismatch: got '{actual_value}', expected '{expected_unit}'")
        
        return True, is_valid
        
    except Exception as e:
        log_print(f"Failed to set unit: {e}")
        return False, False


if __name__ == "__main__":
    # Test: set unit with transferred_unit="1" (default=EA)
    success, is_valid = set_unit("2")
    if success and is_valid:
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
