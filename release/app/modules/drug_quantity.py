"""
Pioneer Drug Quantity Module
Types quantity in the Quantity field and validates
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


def set_quantity(quantity):
    """
    Type quantity in the Quantity field and validate.
    
    Args:
        quantity: Quantity value to type
    
    Returns:
        tuple: (success: bool, is_valid: bool)
    """
    global _app
    
    if not connect_to_pioneer():
        return False, False
    
    try:
        # Screen Selector: Edit/Fill Rx window
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Quantity field
        qty_field = edit_rx_window.child_window(auto_id="uxQuantityPrescribed", control_type="Edit")
        qty_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{BACKSPACE}" * 3)
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(quantity))
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Validate: read back value (legacy Value first, window_text returns label)
        actual_value = qty_field.legacy_properties().get('Value', '')
        log_print(f"Quantity set: '{actual_value}' (expected: '{quantity}')")
        
        is_valid = str(quantity) in actual_value.strip()
        if is_valid:
            log_print(f"✓ Quantity validated: '{actual_value}'")
        else:
            log_print(f"✗ Quantity mismatch: got '{actual_value}', expected '{quantity}'")
        
        return True, is_valid
        
    except Exception as e:
        log_print(f"Failed to set quantity: {e}")
        return False, False


if __name__ == "__main__":
    success, is_valid = set_quantity("1")
    if success and is_valid:
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
