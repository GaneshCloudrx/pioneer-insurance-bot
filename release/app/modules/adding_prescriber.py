"""
Pioneer Adding Prescriber Module
Clicks Add button, selects prescriber type, and saves
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from pywinauto import Desktop
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
                title_re=".*(Edit|Fill Rx|Edit Prescriber|Search For a Prescriber).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_add_prescriber():
    """
    Click the Add button in the prescriber panel.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit/Fill Rx window
        edit_rx_window = _app.window(title_re=".*(Edit|Fill Rx|Search For a Prescriber).*")
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Prescriber AddButton (Name="Supervisor:")
        add_button = edit_rx_window.child_window(title="Supervisor:", auto_id="AddButton", control_type="Button")
        add_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Add prescriber button clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click add prescriber button: {e}")
        return False


def set_prescriber_type(prescriber_type="M.D."):
    """
    Select prescriber type in the Edit Prescriber window.
    
    Args:
        prescriber_type: Type to select (default: "M.D.")
    
    Returns:
        bool: True if typed successfully
    """
    try:
        # Screen Selector: Find Edit Prescriber popup via Desktop (nested windows)
        desktop = Desktop(backend="uia")
        popup_window = desktop.window(title_re=config.SELECTOR_EDIT_PRESCRIBER)
        popup_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Prescriber Type combo box via legacy_properties (Value="<Choose>")
        for desc in popup_window.descendants():
            try:
                props = desc.legacy_properties()
                if props.get('Name') == 'Prescriber Type:' and props.get('Role') == 42:
                    desc.click_input()
                    time.sleep(config.TIMEOUT_AFTER_TYPE)
                    send_keys(prescriber_type, with_spaces=True)
                    time.sleep(config.TIMEOUT_AFTER_CLICK)
                    send_keys("{TAB}")
                    time.sleep(config.TIMEOUT_AFTER_CLICK)
                    log_print(f"✓ Prescriber type set to '{prescriber_type}'")
                    return True
            except Exception:
                continue
        
        log_print("Prescriber Type textbox not found")
        return False
        
    except Exception as e:
        log_print(f"Failed to set prescriber type: {e}")
        return False


def click_save_and_close():
    """
    Click Save & Close button on Edit Prescriber window.
    
    Returns:
        bool: True if clicked successfully
    """
    try:
        # Screen Selector: Find Edit Prescriber popup via Desktop
        desktop = Desktop(backend="uia")
        popup_window = desktop.window(title_re=config.SELECTOR_EDIT_PRESCRIBER)
        popup_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Save & Close button via legacy_properties
        for desc in popup_window.descendants():
            try:
                props = desc.legacy_properties()
                if props.get('Name') == 'Save & Close - F12' and props.get('Role') == 43:
                    desc.click_input()
                    time.sleep(0.5)
                    log_print("✓ Save and Close clicked")
                    return True
            except Exception:
                continue
        
        log_print("Save and Close button not found")
        return False
        
    except Exception as e:
        log_print(f"Failed to click Save and Close: {e}")
        return False


def click_cancel():
    """
    Click Cancel - ESC button to close Edit Prescriber window.
    
    Returns:
        bool: True if clicked successfully
    """
    try:
        # Screen Selector: Find Edit Prescriber popup via Desktop
        desktop = Desktop(backend="uia")
        popup_window = desktop.window(title_re=config.SELECTOR_EDIT_PRESCRIBER)
        popup_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Cancel button via legacy_properties
        for desc in popup_window.descendants():
            try:
                props = desc.legacy_properties()
                if props.get('Name') == 'Cancel - ESC' and props.get('Role') == 43:
                    desc.click_input()
                    time.sleep(0.5)
                    log_print("✓ Cancel clicked")
                    
                    # Click No on "Save Changes?" popup
                    save_dialog = popup_window.child_window(title="Save Changes?")
                    no_button = save_dialog.child_window(title="No", control_type="Button")
                    no_button.click_input()
                    time.sleep(0.5)
                    log_print("✓ Save Changes - No clicked")
                    return True
            except Exception:
                continue
        
        log_print("Cancel button not found")
        return False
        
    except Exception as e:
        log_print(f"Failed to click Cancel: {e}")
        return False


if __name__ == "__main__":
    steps = [click_add_prescriber, set_prescriber_type, click_save_and_close]
    for step in steps:
        if not step():
            log_print(f"\n✗ FAILED at {step.__name__}")
            break
    else:
        log_print("\n✓ ALL STEPS PASSED")
