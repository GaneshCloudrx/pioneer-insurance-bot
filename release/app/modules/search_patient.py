"""
Pioneer Search Patient Module
Clicks the binocular search icon, fills patient search form, and selects patient
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
                title_re=".*(Edit|Fill Rx|Search for Patients).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_search():
    """
    Click the binocular search button in Edit an Rx window.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit an Rx window
        edit_rx_window = _app.window(title_re=".*(Edit|Fill Rx|Search for Patients).*")
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Patient panel > Advanced Search button (binocular icon)
        patient_panel = edit_rx_window.child_window(auto_id="uxPatientPanel")
        search_button = patient_panel.child_window(auto_id="AdvancedSearchButton", control_type="Button")
        search_button.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        search_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Search button clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click search button: {e}")
        return False


def search_and_select_patient(first_name, last_name, dob_month, dob_day, dob_year, phone_area_code, phone_prefix, phone_suffix):
    """
    Fill patient search form, search, and double click first result.
    
    Args:
        first_name: Patient first name
        last_name: Patient last name
        dob_month: DOB month (MM)
        dob_day: DOB day (DD)
        dob_year: DOB year (YYYY)
        phone_area_code: Phone area code
        phone_prefix: Phone prefix
        phone_suffix: Phone suffix
    
    Returns:
        tuple: (success: bool, is_new_patient: bool)
    """
    global _app
    

    try:
        # Reconnect fresh — search window is a new top-level window
        _app = Application(backend="uia").connect(
            title_re=config.SELECTOR_SEARCH_PATIENT,
            timeout=config.TIMEOUT_SEARCH_WINDOW
        )
        search_window = _app.window(title_re=config.SELECTOR_SEARCH_PATIENT)
        #search_window.wait('visible', timeout=config.TIMEOUT_SEARCH_WINDOW)
        search_window.set_focus()
        #time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        dob_panel = search_window.child_window(auto_id="uxDateofBirth")
        phone_panel = search_window.child_window(title="Phone:", control_type="Pane")
        
        for ctrl, val in [
            (search_window.child_window(auto_id="uxFirstName", control_type="Edit"), first_name),
            (search_window.child_window(auto_id="uxLastName", control_type="Edit"), last_name),
            (dob_panel.child_window(auto_id="uxFirstEntry", control_type="Edit"), dob_month),
            (dob_panel.child_window(auto_id="uxMiddleEntry", control_type="Edit"), dob_day),
            (dob_panel.child_window(auto_id="uxLastEntry", control_type="Edit"), dob_year),
            (phone_panel.child_window(auto_id="uxFirstEntry", control_type="Edit"), phone_area_code),
            (phone_panel.child_window(auto_id="uxMiddleEntry", control_type="Edit"), phone_prefix),
            (phone_panel.child_window(auto_id="uxLastEntry", control_type="Edit"), phone_suffix),
        ]:
            ctrl.set_edit_text(val)
        
        # Click Search and wait for results
        search_btn = search_window.child_window(auto_id="uxSearch", control_type="Button")
        search_btn.click_input()
        time.sleep(3)
        log_print("✓ Patient search submitted")

        # Find results table and double-click first row
        try:
            results_table = search_window.child_window(auto_id="uxSearchResults", control_type="Table")
            results_table.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)

            table_rows = results_table.children(control_type="Custom")
            if not table_rows:
                table_rows = results_table.children(control_type="DataItem")
            if not table_rows:
                table_rows = results_table.children(control_type="TableRow")

            if table_rows:
                first_row = table_rows[0]
                first_row.set_focus()
                time.sleep(0.2)
                first_row.double_click_input()
                time.sleep(0.5)
                log_print("✓ Patient selected")
                return True, False
            else:
                raise Exception("No rows found")

        except Exception:
            log_print("✗ No patient found - new patient")
            send_keys("{ESC}")
            time.sleep(0.5)
            return True, True
        
    except Exception as e:
        log_print(f"Failed to search patient: {e}")
        return False, False


if __name__ == "__main__":
    # Test: click search icon then fill form
    if click_search():
        #'patient': {'first_name': 'Briyanna', 'middle_name': None, 'last_name': 'Gunner', 'gender': None, 'phone': '4692740404', 'dob': '1992-05-28', 'street': '12720 Rivington Dr', 'city': 'Farmers Branch', 'state': 'TX', 'zip': '75234', 'email': None, 'country': 'USA'}
        time.sleep(1)
        success, is_new_patient = search_and_select_patient("Briyanna", "Gunner", "05", "28", "1992", "469", "274", "0404")
        if success:
            log_print(f"\n✓ TEST PASSED | New Patient: {is_new_patient}")
        else:
            log_print("\n✗ TEST FAILED")
    else:
        log_print("\n✗ TEST FAILED - Could not open search")
