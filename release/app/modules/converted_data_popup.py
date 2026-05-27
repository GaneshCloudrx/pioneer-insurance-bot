"""
Pioneer Converted Data Popup Handler
Clicks OK if Conversion Review popup appears inside Fill Requests window
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
                title_re=".*(Fill Requests|Edit an Rx).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_ok_conversion():
    """
    Click OK on Conversion Review popup if it appears.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Fill Requests window
        fill_requests_window = _app.window(title_re=".*(Fill Requests|Edit an Rx).*")
        fill_requests_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        
        # Target Selector: ConversionReviewDialog > OK button
        conversion_dialog = fill_requests_window.child_window(auto_id="ConversionReviewDialog")
        conversion_dialog.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        
        ok_button = conversion_dialog.child_window(auto_id="uxOk", control_type="Button")
        ok_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Conversion Review popup OK clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click OK on Conversion Review popup: {e}")
        return False


if __name__ == "__main__":
    if click_ok_conversion():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
