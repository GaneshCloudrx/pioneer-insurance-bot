"""
Pioneer Duplicate Prescriber Popup Handler
Clicks No if Duplicate Detected popup appears inside Edit Prescriber
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
                title_re=config.SELECTOR_EDIT_PRESCRIBER,
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_no_duplicate():
    """
    Click No on Duplicate Detected popup if it appears.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit Prescriber window
        edit_prescriber_window = _app.window(title_re=config.SELECTOR_EDIT_PRESCRIBER)
        
        # Target Selector: Duplicate Detected window > No button
        duplicate_window = edit_prescriber_window.child_window(title="Duplicate Detected!")
        no_button = duplicate_window.child_window(title="No", control_type="Button")
        no_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Duplicate Detected popup - No clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click No on Duplicate Detected popup: {e}")
        return False


if __name__ == "__main__":
    if click_no_duplicate():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
