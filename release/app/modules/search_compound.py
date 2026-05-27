"""
Pioneer Compound Search Module
Opens compound search, types NDC in Alternate ID, searches, and selects first result or cancels
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer."""
    global _app
    try:
        if _app is None:
            _app = Application(backend="uia").connect(
                title_re=".*(Edit|Fill Rx|Search For a Prescriber|Search for a Patient|Fill Requests).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def search_compound(ndc):
    """
    Click drug binocular (reuses search_drug Step 1), wait for compound window,
    type NDC in Alternate ID field, search, and select first row or cancel.

    Args:
        ndc: NDC string to search (e.g. "10101-0011-99")

    Returns:
        tuple: (success: bool, compound_found: bool)
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    try:
        # Step 1: Click binocular search button on Edit Rx window
        edit_window = _app.window(title_re=".*(Edit|Fill Rx|Search For a Prescriber|Search for a Patient|Fill Requests).*")
        edit_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        search_icon = edit_window.child_window(auto_id="AdvancedSearchButton", title="Expire:", control_type="Button")
        search_icon.click_input()
        time.sleep(0.5)
        log_print("✓ Drug search binocular clicked")

        # Step 2: Wait for compound search window
        search_window = _app.window(title="Search For Compounds")
        search_window.wait('visible', timeout=config.TIMEOUT_SEARCH_WINDOW)
        search_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        log_print("✓ Compound search window visible")

        # Step 3: Type NDC in Alternate ID field and search
        alt_id_field = search_window.child_window(auto_id="uxAlternateID", control_type="Edit")
        alt_id_field.set_edit_text(str(ndc))
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        search_window.child_window(auto_id="uxSearch", control_type="Button").click_input()
        time.sleep(config.TIMEOUT_AFTER_SEARCH)
        log_print(f"✓ Searched for NDC: {ndc}")

        # Step 3b: Check for first row and double-click, or cancel
        try:
            first_row = search_window.child_window(title="Table row 1", control_type="Custom")
            first_row.wait('exists', timeout=config.TIMEOUT_ELEMENT_EXISTS)
            first_row.click_input(double=True)
            time.sleep(config.TIMEOUT_AFTER_CLICK)
            send_keys("{ENTER}")
            time.sleep(0.5)
            log_print("✓ Compound selected from first row")
            return True, True

        except Exception:
            log_print("✗ Compound not found")
            send_keys("{ESC}")
            time.sleep(config.TIMEOUT_AFTER_CLICK)
            log_print("Cancel clicked")
            return True, False

    except Exception as e:
        log_print(f"Failed compound search: {e}")
        return False, False


if __name__ == "__main__":
    success, found = search_compound("15101-0011-99")
    if success:
        log_print(f"\n✓ TEST PASSED (compound_found={found})")
    else:
        log_print("\n✗ TEST FAILED")
