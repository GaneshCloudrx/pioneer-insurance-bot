"""
Pioneer Patient Profile Module
Checks if patient textbox contains expected first name from API response
"""
import time
from pywinauto.application import Application
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
                title_re=config.SELECTOR_EDIT_RX,
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def check_patient_name(api_first_name):
    """
    Check if patient textbox contains expected first name from API response.
    
    Args:
        api_first_name: First name from API response to match against
    
    Returns:
        bool: True if textbox has patient name and contains the first name
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit an Rx window
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Patient quick search textbox
        patient_textbox = edit_rx_window.child_window(auto_id="uxPatientQuickSearch", control_type="Edit")
        patient_textbox.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        
        # Get textbox value
        patient_value = patient_textbox.get_value()
        log_print(f"Patient textbox value: '{patient_value}'")
        
        # Step 1: Check if empty or null
        if not patient_value or patient_value.strip() == "":
            log_print("Patient textbox is empty")
            return False
        
        # Step 2: Check if first name from API matches
        if api_first_name.strip().lower() in patient_value.strip().lower():
            log_print(f"✓ First name '{api_first_name}' found in '{patient_value}'")
            return True
        else:
            log_print(f"✗ First name '{api_first_name}' NOT found in '{patient_value}'")
            return False
        
    except Exception as e:
        log_print(f"Failed to check patient name: {e}")
        return False


if __name__ == "__main__":
    # Test with hardcoded first name (replace with API value later)
    if check_patient_name("Carolyn"):
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
