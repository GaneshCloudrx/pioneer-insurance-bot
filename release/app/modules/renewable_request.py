"""
Pioneer Renewable Request Popup Handler
Clicks Cancel if Rx Renew popup appears inside Fill Requests window
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
                timeout=config.TIMEOUT_POPUP_CHECK
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_cancel_renew():
    """
    Click Cancel on Rx Renew popup if it appears.
    
    Returns:
        bool: True if cancelled successfully
    """
    global _app
    
    if not connect_to_pioneer():
        log_print(f"Failed to cancel Renewable Request popup: {e}")
        return False
    
    try:
        # Screen Selector: Fill Requests window
        fill_requests_window = _app.window(title_re=".*(Fill Requests|Edit an Rx).*")
        fill_requests_window.wait('visible', timeout=config.TIMEOUT_POPUP_CHECK)
        
        # Target Selector: RxRenewDialog > Cancel button
        renew_dialog = fill_requests_window.child_window(auto_id="RxRenewDialog")
        renew_dialog.wait('visible', timeout=config.TIMEOUT_POPUP_CHECK)
        
        cancel_button = renew_dialog.child_window(auto_id="uxCancel", control_type="Button")
        cancel_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Renewable Request popup cancelled")
        return True
        
    except Exception as e:
        log_print(f"Failed to cancel Renewable Request popup: {e}")
        return False


if __name__ == "__main__":
    if click_cancel_renew():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
