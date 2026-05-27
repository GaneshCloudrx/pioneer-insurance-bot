"""
Pioneer Drug SIG Module
Types SIG (directions) in the SIG field and validates
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


def set_sig(sig_text):
    """
    Type SIG directions in the SIG field and validate.
    
    Args:
        sig_text: SIG directions text to type
    
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
        
        # Target Selector: SIG field (RichEdit document)
        try:
            sig_field = edit_rx_window.child_window(auto_id="uxDirectionsSigCodes")
            sig_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        except Exception:
            sig_field = edit_rx_window.child_window(class_name_re=".*RichEdit20W.*", found_index=0)
            sig_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        
        sig_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("^a")
        time.sleep(0.1)
        send_keys("{BACKSPACE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(sig_text, with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{TAB}")
        time.sleep(0.5)
        
        # Validate: read back value
        try:
            actual_value = sig_field.legacy_properties().get('Value', '')
        except Exception:
            actual_value = sig_field.window_text()
        log_print(f"SIG set: '{actual_value}' (expected: '{sig_text}')")
        
        is_valid = sig_text.strip().lower() in actual_value.strip().lower()
        if is_valid:
            log_print(f"✓ SIG validated: '{actual_value}'")
        else:
            log_print(f"✗ SIG mismatch: got '{actual_value}', expected '{sig_text}'")
        
        return True, is_valid
        
    except Exception as e:
        log_print(f"Failed to set SIG: {e}")
        return False, False


if __name__ == "__main__":
    success, is_valid = set_sig("Inject 3-4 vials subcutaneously daily")
    if success and is_valid:
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
