"""
Pioneer Priority Window Popup Handler
Clicks Cancel if a Priority popup window appears
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
                title_re=config.SELECTOR_EDIT_RX_FULL,
                timeout=config.TIMEOUT_POPUP_CHECK
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_cancel_priority():
    """
    Click Cancel - ESC button if Priority popup window appears.
    
    Returns:
        bool: True if cancelled or window not found (no action needed)
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit an Rx window
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_POPUP_CHECK)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: RxPromiseTimeDialog > Cancel button
        priority_dialog = edit_rx_window.child_window(auto_id="RxPromiseTimeDialog")
        cancel_button = priority_dialog.child_window(auto_id="uxCancel", control_type="Button")
        cancel_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Priority popup cancelled")
        return True
        
    except Exception as e:
        log_print(f"Failed to cancel priority popup: {e}")
        return False


if __name__ == "__main__":
    if click_cancel_priority():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
