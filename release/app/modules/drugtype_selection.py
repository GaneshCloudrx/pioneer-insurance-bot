"""
Pioneer Drug Type Selection Module
Selects drug type (Compound or Specific Drug) and validates selection
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
                title_re=".*(Edit|Fill Rx|Search For a Prescriber|Search for a Patient).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def select_drug_type(is_compound=False):
    """
    Select drug type in Edit Rx window and validate.
    If is_compound=True, types "Compound", otherwise "Specific Drug".
    
    Args:
        is_compound: True if compound (drug_type=1), False for specific drug
    
    Returns:
        tuple: (success: bool, is_valid: bool)
    """
    global _app
    
    if not connect_to_pioneer():
        return False, False
    
    expected_type = "Compound" if is_compound else "Specific Drug"
    
    try:
        # Screen Selector: Edit/Fill Rx window
        edit_rx_window = _app.window(title_re=".*(Edit|Fill Rx|Search For a Prescriber|Search for a Patient).*")
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Type combo box Edit field (Name="Type:", Role=42)
        type_edit = edit_rx_window.child_window(title="Type:", control_type="ComboBox")
        type_field = type_edit.child_window(auto_id="1001", control_type="Edit")
        type_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{BACKSPACE}" * 2)
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(expected_type, with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}{ENTER}")
        time.sleep(0.5)
        
        # Validate: read back from combo box (try multiple methods)
        actual_value = (
            type_edit.legacy_properties().get('Value', '') or
            type_field.window_text() or
            type_field.legacy_properties().get('Value', '')
        )
        log_print(f"Drug type set: '{actual_value}' (expected: '{expected_type}')")
        
        is_valid = expected_type.lower() in actual_value.strip().lower()
        if is_valid:
            log_print(f"✓ Drug type validated: '{actual_value}'")
        else:
            log_print(f"✗ Drug type mismatch: got '{actual_value}', expected '{expected_type}'")
        
        return True, is_valid
        
    except Exception as e:
        log_print(f"Failed to select drug type: {e}")
        return False, False


if __name__ == "__main__":
    # Test: select Specific Drug (is_compound=False)
    success, is_valid = select_drug_type(is_compound=True)
    if success and is_valid:
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
