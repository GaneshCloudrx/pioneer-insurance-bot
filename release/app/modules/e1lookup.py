"""
Pioneer E1 Lookup Module
Performs Patient Eligibility Check via Action toolbar shortcut
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
                title_re=config.SELECTOR_EDIT_RX_FULL,
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def e1_lookup():
    """
    Perform E1 eligibility lookup:
    1. Click Action toolbar, send pp+Enter+Enter
    2. Type "Eli" in Third Party combo, Tab
    3. Click first Next
    4. Check for NON-MATCHED — cancel if found
    5. Loop through insurance pages clicking Next (max 3)
    6. Click Confirm & Close

    Returns:
        tuple: (success: bool, is_matched: bool)
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False, False

    try:
        # Step 1: Click Action Toolbar and send shortcut
        edit_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        edit_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        toolbar = edit_window.child_window(auto_id="uxWorkAreaButtonsToolStrip", control_type="ToolBar")
        rect = toolbar.rectangle()
        toolbar.click_input(coords=(20, (rect.height() // 2)))
        time.sleep(0.5)

        # Step 2: Send pp, Enter, Enter with gaps
        send_keys("p")
        time.sleep(0.5)
        send_keys("p")
        time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(0.5)
        log_print("✓ Action toolbar shortcut sent")

        # Step 3: Wait for Patient Eligibility Check window, type "Eli" in Third Party combo
        elig_window = edit_window.child_window(title_re=config.SELECTOR_ELIGIBILITY, control_type="Window")
        elig_window.wait('visible', timeout=config.TIMEOUT_E1_LOOKUP)
        elig_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        tp_combo = elig_window.child_window(title="<Choose Third Party>", control_type="ComboBox")
        tp_edit = tp_combo.child_window(auto_id="1001", control_type="Edit")
        tp_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("Eli", with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{TAB}")
        time.sleep(0.5)
        log_print("✓ Third Party set to 'Eli'")

        # Step 4: Click first Next button
        next_btn = elig_window.child_window(auto_id="uxNext", control_type="Button")
        next_btn.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        next_btn.click_input()
        time.sleep(2)
        log_print("✓ First Next clicked")

        # Step 5: Check for NON-MATCHED in plan detail
        try:
            error_label = elig_window.child_window(auto_id="uxErrorInformation", control_type="Text")
            plan_detail = error_label.window_text()
            log_print(f"Plan detail: '{plan_detail}'")

            if "non-matched" in plan_detail.lower():
                log_print("✗ NON-MATCHED found — cancelling")
                elig_window.child_window(auto_id="uxCancel", control_type="Button").click_input()
                time.sleep(0.5)
                return True, False
        except Exception:
            pass

        # Step 6: Loop through insurance pages (max 3)
        for i in range(3):
            try:
                tp_field = elig_window.child_window(auto_id="uxThirdPartyQuickSearch", control_type="Edit")
                if not tp_field.exists(timeout=2):
                    break
                tp_value = tp_field.legacy_properties().get('Value', '')
                log_print(f"  Insurance {i+1}: '{tp_value}'")

                next_btn = elig_window.child_window(auto_id="uxNext", control_type="Button")
                next_btn.click_input()
                time.sleep(2)
                log_print(f"✓ Next clicked for insurance {i+1}")

                # Check NON-MATCHED again after each Next
                try:
                    error_label = elig_window.child_window(auto_id="uxErrorInformation", control_type="Text")
                    plan_detail = error_label.window_text()
                    if "non-matched" in plan_detail.lower():
                        log_print("✗ NON-MATCHED found — cancelling")
                        elig_window.child_window(auto_id="uxCancel", control_type="Button").click_input()
                        time.sleep(0.5)
                        return True, False
                except Exception:
                    pass

            except Exception:
                break

        # Step 7: Click Confirm & Close
        confirm_btn = elig_window.child_window(auto_id="uxConfirmAndClose", control_type="Button")
        confirm_btn.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        confirm_btn.click_input()
        time.sleep(0.5)
        log_print("✓ Confirm & Close clicked")

        return True, True

    except Exception as e:
        log_print(f"Failed E1 lookup: {e}")
        return False, False


if __name__ == "__main__":
    success, matched = e1_lookup()
    if success and matched:
        log_print("\n✓ TEST PASSED")
    elif success:
        log_print("\n✗ E1 LOOKUP FAILED (NON-MATCHED)")
    else:
        log_print("\n✗ TEST FAILED")
