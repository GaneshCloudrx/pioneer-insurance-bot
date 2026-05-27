"""
Select RPh Pharmacist Module
Selects the RPh (Registered Pharmacist) in the ComboBox on the Edit Rx window.
Ported from CloudRx DE bot dispense.py RPh selection logic.
"""
import time
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer via shared cache."""
    global _app
    try:
        _app = get_pioneer_app()
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def select_rph(rph_name=None):
    """
    Select RPh pharmacist in the RPh ComboBox on the Edit Rx window.

    Args:
        rph_name: Pharmacist name to select. Defaults to config.RPH_NAME.

    Returns:
        bool: True if selected successfully, False otherwise
    """
    global _app
    _app = None

    if rph_name is None:
        rph_name = config.RPH_NAME

    if not rph_name:
        log_print("✗ RPh name not configured (set RPH_NAME or PIONEER_ID_NAME in .env)")
        return False

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        rph_combo = window.child_window(title="RPh:", control_type="ComboBox")
        rph_edit = rph_combo.child_window(auto_id="1001", control_type="Edit")
        rph_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(rph_name), with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        log_print(f"✓ RPh selected: {rph_name}")
        return True

    except Exception as e:
        log_print(f"Failed to select RPh: {e}")
        _app = None
        return False


if __name__ == "__main__":
    if select_rph():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
