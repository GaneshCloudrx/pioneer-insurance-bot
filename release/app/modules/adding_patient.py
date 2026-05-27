"""
Pioneer Adding Patient Module
Clicks the Add button to add a new patient
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from pywinauto import Desktop, mouse
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
                title_re=".*(Edit Patient|Fill Rx|Search for Patients).*",
                timeout=config.TIMEOUT_ELEMENT_EXISTS
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_add_patient():
    """
    Click the Add button in the patient panel.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Search for Patients window
        search_window = _app.window(title_re=".*(Edit Patient|Fill Rx|Search for Patients).*")
        #search_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        search_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: AddButton inside uxPatientPanel
        patient_panel = search_window.child_window(auto_id="uxPatientPanel")
        add_button = patient_panel.child_window(auto_id="AddButton", control_type="Button")
        #add_button.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        add_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Add patient button clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click add patient button: {e}")
        return False


def set_patient_notification():
    """
    Type 'Ask Patient?' in the Notification combo box on Edit Patient window.
    
    Returns:
        bool: True if typed successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit Patient window (top-level)
        edit_patient_window = _app.window(title_re=config.SELECTOR_EDIT_PATIENT)
        edit_patient_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_patient_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Notification combo box > Edit field (auto_id=1001)
        notification_combo = edit_patient_window.child_window(title="Notification:", control_type="ComboBox")
        notification_edit = notification_combo.child_window(auto_id="1001", control_type="Edit")
        notification_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{BACKSPACE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("Ask")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        return True
    except Exception as e:
        log_print(f"Failed to set Patient Notification: {e}")
        return False

def click_categories_tab(category="ENCINO PHARMACY"):
    """
    Click Categories tab and type category in the Choose Categories combo box.
    
    Args:
        category: Category name to type (from API response)
    
    Returns:
        bool: True if clicked and typed successfully
    """
    try:
        # Screen Selector: Find Edit Patient popup via Desktop (bypasses nested window issue)
        desktop = Desktop(backend="uia")
        popup_window = desktop.window(title_re=config.SELECTOR_EDIT_PATIENT)
        popup_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Step 1: Find the Tab Control
        patient_tab_control = popup_window.child_window(
            auto_id="cntPatientTabControl",
            control_type="Tab"
        )
        
        # Step 2: Find Categories TabItem in children
        for tab in patient_tab_control.children(control_type="TabItem"):
            try:
                tab_name = tab.legacy_properties().get('Name', '')
            except Exception:
                tab_name = tab.element_info.name
            
            if tab_name == "Categories" or tab.window_text() == "Categories":
                tab.set_focus()
                time.sleep(0.1)
                tab.click_input()
                time.sleep(config.TIMEOUT_AFTER_CLICK)
                log_print("✓ Categories tab clicked")
                break
        else:
            log_print("Categories tab not found")
            return False
        
        # Step 3: Find "Choose Categories:" toolbar via legacy_properties, click relative to it
        toolbar = None
        for desc in popup_window.descendants():
            try:
                props = desc.legacy_properties()
                if props.get('Name') == 'Choose Categories:' and props.get('Role') == 22:
                    toolbar = desc
                    break
            except Exception:
                continue
        
        if not toolbar:
            log_print("Choose Categories toolbar not found")
            return False
        
        # Click relative: MiddleRight with OffsetX=-231 (same as Power Automate)
        rect = toolbar.rectangle()
        click_x = rect.right - 231
        click_y = (rect.top + rect.bottom) // 2
        mouse.click(coords=(click_x, click_y))
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(category, with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        log_print(f"✓ Category '{category}' typed")
        return True
        
    except Exception as e:
        log_print(f"Failed to click Categories tab: {e}")
        return False


def click_save_and_close():
    """
    Click Save and Close button on Edit Patient window.
    
    Returns:
        bool: True if clicked successfully
    """
    try:
        # Screen Selector: Find Edit Patient popup via Desktop
        desktop = Desktop(backend="uia")
        popup_window = desktop.window(title_re=config.SELECTOR_EDIT_PATIENT)
        popup_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: uxSave button via legacy_properties
        for desc in popup_window.descendants():
            try:
                props = desc.legacy_properties()
                if props.get('Name') == 'Save & Close - F12' and props.get('Role') == 43:
                    desc.click_input()
                    time.sleep(0.5)
                    break
            except Exception:
                continue
        else:
            log_print("Save and Close button not found")
            return False
        
        log_print("✓ Save and Close clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click Save and Close: {e}")
        return False


def click_cancel():
    """
    Click Cancel - ESC button to close Edit Patient window, then No on Save Changes.
    
    Returns:
        bool: True if clicked successfully
    """
    try:
        # Screen Selector: Find Edit Patient popup via Desktop
        desktop = Desktop(backend="uia")
        popup_window = desktop.window(title_re=config.SELECTOR_EDIT_PATIENT)
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
    #        #'patient': {'first_name': 'Briyanna', 'middle_name': None, 'last_name': 'Gunner', 'gender': None, 'phone': '4692740404', 'dob': '1992-05-28', 'street': '12720 Rivington Dr', 'city': 'Farmers Branch', 'state': 'TX', 'zip': '75234', 'email': None, 'country': 'USA'}

    steps = [click_add_patient, set_patient_notification, click_save_and_close]
    for step in steps:
        if not step():
            log_print(f"\n✗ FAILED at {step.__name__}")
            break
    else:
        log_print("\n✓ ALL STEPS PASSED")
