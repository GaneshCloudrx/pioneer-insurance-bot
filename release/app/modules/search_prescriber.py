"""
Pioneer Search Prescriber Module
Clicks the binocular search icon, fills prescriber search form, and selects prescriber
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
                title_re=".*(Edit|Fill Rx|Search For a Prescriber).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_search():
    """
    Click the prescriber binocular search button in Edit Rx window.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        # Screen Selector: Edit/Fill Rx window
        edit_rx_window = _app.window(title_re=".*(Edit|Fill Rx|Search For a Prescriber).*")
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Prescriber AdvancedSearchButton (Name="Supervisor:")
        search_button = edit_rx_window.child_window(title="Supervisor:", auto_id="AdvancedSearchButton", control_type="Button")
        #search_button.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        search_button.click_input()
        time.sleep(0.5)
        
        log_print("✓ Prescriber search button clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click prescriber search button: {e}")
        return False


def search_and_select_prescriber(npi, state="", zip_code=""):
    #zip code should be only first five digits
    zip_code = str(zip_code)[:5]
    """
    Fill prescriber search form, search, and double click first result.
    
    Args:
        npi: Prescriber NPI number
        state: Prescriber state (optional)
        zip_code: Prescriber zip code (optional)
    
    Returns:
        tuple: (success: bool, is_new_prescriber: bool)
    """
    global _app
    
    if not connect_to_pioneer():
        return False, False
    
    try:
        # Reconnect fresh — search window is a new top-level window
        _app = Application(backend="uia").connect(
            title_re=config.SELECTOR_SEARCH_PRESCRIBER,
            timeout=config.TIMEOUT_SEARCH_WINDOW
        )
        search_window = _app.window(title_re=config.SELECTOR_SEARCH_PRESCRIBER)
        search_window.wait('visible', timeout=config.TIMEOUT_SEARCH_WINDOW)
        search_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Fill fields
        search_window.child_window(auto_id="uxNPI", control_type="Edit").set_edit_text(npi)
        if state:
            search_window.child_window(auto_id="uxState", control_type="Edit").set_edit_text(state)
        if zip_code:
            search_window.child_window(auto_id="uxZipCode", control_type="Edit").set_edit_text(zip_code)

        # Click Search
        search_btn = search_window.child_window(auto_id="uxSearch", control_type="Button")
        search_btn.click_input()
        time.sleep(3)
        log_print("✓ Prescriber search submitted")

        # Find results table and double-click first row
        try:
            results_table = search_window.child_window(auto_id="uxSearchResults", control_type="Table")
            results_table.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)

            # Try multiple control types for rows (Infragistics grid varies)
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
                log_print("✓ Prescriber selected")
                return True, False
            else:
                raise Exception("No rows found")

        except Exception:
            log_print(f"✗ No prescriber found for NPI: {npi}")
            send_keys("{ESC}")
            time.sleep(0.5)
            return True, True

    except Exception as e:
        log_print(f"Failed to search prescriber: {e}")
        return False, False


if __name__ == "__main__":
    # Test: click search icon then fill form
    if click_search():
        #{'first_name': 'Gary', 'last_name': 'Hubert', 'NPI': '1386668507', 'address_line1': '225 W Hillcrest Drive Suite 201', 'address_line2': None, 'address_city': 'Thousand Oaks', 'address_country': 'US', 'address_postal_code': '913607883', 'address_state': 'CA',
        time.sleep(1)
        success, is_new = search_and_select_prescriber("1386668507", "CA", "913607883")
        if success:
            log_print(f"\n✓ TEST PASSED | New Prescriber: {is_new}")
        else:
            log_print("\n✗ TEST FAILED")
    else:
        log_print("\n✗ TEST FAILED - Could not open search")
