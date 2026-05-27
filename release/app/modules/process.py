"""
Pioneer Process Module
Clicks the Process - F2 button in Fill Requests window
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
                title_re=config.SELECTOR_FILL_REQUESTS,
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_process():
    """
    Click the Process - F2 button in Fill Requests window.
    
    Returns:
        bool: True if successful
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Fill Requests window
        fill_requests_window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        fill_requests_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        fill_requests_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Process - F2 button
        process_button = fill_requests_window.child_window(auto_id="uxProcess", control_type="Button")
        process_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Process button clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click Process button: {e}")
        return False


if __name__ == "__main__":
    if click_process():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
