"""
Pioneer Duplicate Patient Popup Handler
Clicks Cancel if Duplicate Patients window appears inside Edit Patient
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
                title_re=config.SELECTOR_EDIT_PATIENT,
                timeout=config.TIMEOUT_ELEMENT_EXISTS
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_cancel_duplicate():
    """
    Click Cancel on Duplicate Patients popup if it appears.
    
    Returns:
        bool: True if cancelled successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit Patient window
        edit_patient_window = _app.window(title_re=config.SELECTOR_EDIT_PATIENT)
        #edit_patient_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        
        # Target Selector: Duplicate Patients window > Cancel button
        duplicate_window = edit_patient_window.child_window(title="Duplicate Patients")
        #duplicate_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        
        cancel_button = duplicate_window.child_window(auto_id="uxCancel", control_type="Button")
        cancel_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Duplicate Patients popup cancelled")
        return True
        
    except Exception as e:
        log_print(f"Failed to cancel Duplicate Patients popup: {e}")
        return False


if __name__ == "__main__":
    if click_cancel_duplicate():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
