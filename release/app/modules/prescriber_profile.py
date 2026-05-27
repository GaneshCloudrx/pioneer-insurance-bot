"""
Pioneer Prescriber Profile Module
Checks if prescriber textbox contains expected last name from API response
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


def check_prescriber_name(api_last_name):
    """
    Check if prescriber textbox contains expected last name from API response.
    
    Args:
        api_last_name: Last name from API response to match against
    
    Returns:
        bool: True if textbox has prescriber name and contains the last name
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit/Fill Rx window
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Prescriber quick search textbox
        prescriber_textbox = edit_rx_window.child_window(auto_id="uxPrescriberQuickSearch", control_type="Edit")
        prescriber_textbox.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        
        # Get textbox value
        prescriber_value = prescriber_textbox.get_value()
        log_print(f"Prescriber textbox value: '{prescriber_value}'")
        
        # Step 1: Check if empty or null
        if not prescriber_value or prescriber_value.strip() == "":
            log_print("Prescriber textbox is empty")
            return False
        
        # Step 2: Check if last name from API matches
        if api_last_name.strip().lower() in prescriber_value.strip().lower():
            log_print(f"✓ Last name '{api_last_name}' found in '{prescriber_value}'")
            return True
        else:
            log_print(f"✗ Last name '{api_last_name}' NOT found in '{prescriber_value}'")
            return False
        
    except Exception as e:
        log_print(f"Failed to check prescriber name: {e}")
        return False


if __name__ == "__main__":
    # Test with hardcoded last name (replace with API value later)
    if check_prescriber_name("Patel"):
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
