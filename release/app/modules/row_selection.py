"""
Pioneer Row Selection Module
Selects a specific row in Fill Requests table by clicking Request On cell and pressing spacebar
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
                title_re=config.SELECTOR_FILL_REQUESTS,
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def select_row(row_index):
    """
    Select a row in Fill Requests table by clicking the first available matching row
    and pressing spacebar. When multiple elements match (e.g. 2x "Table row 1"),
    clicks the first one that is visible and enabled.

    Args:
        row_index: Row number to select (default: 3)

    Returns:
        bool: True if successful
    """
    global _app

    if not connect_to_pioneer():
        return False

    try:
        log_print(f"Selecting row {row_index}...")

        fill_requests_window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        fill_requests_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Find all matching row elements (e.g. 2 tables can have "Table row 1")
        candidates = fill_requests_window.descendants(
            title=f"Table row {row_index}",
            control_type="Custom"
        )

        row = None
        for c in candidates:
            try:
                if c.is_enabled() and c.is_visible():
                    row = c
                    break
            except Exception:
                continue

        if row is None:
            # Fallback: single grid by id
            grid = fill_requests_window.child_window(auto_id="uxGrid", control_type="Table")
            if not grid.exists(timeout=1):
                grid = fill_requests_window.child_window(auto_id="ultraGridNT1", control_type="Table")
            row = grid.child_window(title=f"Table row {row_index}", control_type="Custom")

        try:
            row.set_focus()
            time.sleep(config.TIMEOUT_AFTER_CLICK)
        except Exception:
            pass

        row.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("{SPACE}")
        time.sleep(0.5)

        log_print(f"✓ Row {row_index} selected")
        return True

    except Exception as e:
        log_print(f"Failed to select row {row_index}: {e}")
        return False

# Test
if __name__ == "__main__":
    if select_row(2):
        log_print("\n✓ TEST PASSED")
        time.sleep(5)
    else:
        log_print("\n✗ TEST FAILED")
