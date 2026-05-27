"""
Patient Filter Module
Filters the Fill Requests grid by patient name via the Patient column header filter.
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
    global _app
    try:
        _app = Application(backend="uia").connect(
            title_re=config.SELECTOR_FILL_REQUESTS,
            timeout=config.TIMEOUT_ELEMENT_VISIBLE
        )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        _app = None
        return False


def filter_by_patient(patient_name):
    """
    Filter Fill Requests grid by patient name.
    1. Click Patient column header (MiddleRight -20px offset)
    2. Tab, Enter, Enter to open filter operand
    3. Type patient name
    4. Enter to apply

    Args:
        patient_name: Patient name to filter by

    Returns:
        bool: True if filter applied successfully
    """
    global _app

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        grid = window.child_window(auto_id="uxGrid", control_type="Table")
        patient_header = grid.child_window(title="Patient", control_type="Header", found_index=0)
        rect = patient_header.rectangle()
        patient_header.click_input(coords=(rect.width() - 20, rect.height() // 2))
        time.sleep(0.5)

        send_keys("{TAB}")
        time.sleep(0.3)
        send_keys("{ENTER}")
        time.sleep(0.3)
        send_keys("{ENTER}")
        time.sleep(0.3)

        operand = window.child_window(title="Operand", control_type="DataItem")
        #operand.wait("exists", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        operand.click_input()
        time.sleep(0.2)
        send_keys(str(patient_name), with_spaces=True)
        time.sleep(0.3)
        send_keys("{ENTER}")
        time.sleep(0.3)

        log_print(f"✓ Patient filter applied: '{patient_name}'")
        return True

    except Exception as e:
        log_print(f"Failed to apply patient filter: {e}")
        _app = None
        return False


if __name__ == "__main__":
    if filter_by_patient("Test Patient"):
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
