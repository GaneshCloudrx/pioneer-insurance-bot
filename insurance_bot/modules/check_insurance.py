"""
Check and Add Insurance Module
Opens Edit Patient, checks if the target insurance exists in the pay methods grid,
and adds it if not present.

This is the core insurance logic — equivalent to the Metro bot's add_insurance.py
but generalized to any insurance payer from the API response.
"""
import time
from pywinauto.keyboard import send_keys
from pywinauto import Desktop
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def click_edit_patient():
    """
    Click the pencil/Edit button on the patient panel to open Edit Patient window.

    Returns:
        bool: True if Edit Patient window opened successfully
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        patient_panel = window.child_window(auto_id="uxPatientPanel")
        edit_btn = patient_panel.child_window(auto_id="EditButton", control_type="Button")
        edit_btn.click_input()
        time.sleep(1)

        log_print("[INSURANCE] Edit Patient button clicked")
        return True

    except Exception as e:
        log_print(f"[INSURANCE] Failed to click Edit Patient: {e}")
        return False


def has_insurance(payer_name):
    """
    Check if the given insurance payer already exists in the patient's pay methods grid.

    Scans the uxPayMethodsGrid table in Edit Patient window for any cell value
    containing the payer name (case-insensitive, first word match).

    Args:
        payer_name: Insurance payer name to search for (e.g. "Aetna", "United Healthcare")

    Returns:
        bool: True if insurance already exists
    """
    search_term = payer_name.strip().split()[0].lower() if payer_name else ""
    if not search_term:
        log_print("[INSURANCE] No payer name to check")
        return False

    try:
        desktop = Desktop(backend="uia")
        edit_window = desktop.window(title_re=config.SELECTOR_EDIT_PATIENT)
        edit_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        grid = edit_window.child_window(auto_id="uxPayMethodsGrid", control_type="Table")
        grid.wait('exists', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        for child in grid.children():
            if not child.window_text().startswith("Row"):
                continue
            for cell in child.children():
                try:
                    val = cell.legacy_properties().get("Value", "")
                    if search_term in val.lower():
                        log_print(f"[INSURANCE] '{payer_name}' already exists in insurance grid")
                        return True
                except Exception:
                    pass

        log_print(f"[INSURANCE] '{payer_name}' not found in insurance grid")
        return False

    except Exception as e:
        log_print(f"[INSURANCE] Failed to check insurance grid: {e}")
        return False


def add_insurance_to_grid(payer_name, bin_number="", pcn="", member_id="", group_number=""):
    """
    Add a new insurance entry to the patient's pay methods grid.

    Flow:
    1. Click on the pay methods grid
    2. Press F2 (New) to add a new entry
    3. Type the payer name and press Enter to search/select
    4. Fill in BIN, PCN, Member ID, Group Number in the Pay Method window
    5. Save the pay method

    Args:
        payer_name: Insurance payer name (e.g. "Aetna")
        bin_number: BIN number (e.g. "610502")
        pcn: PCN value (e.g. "AETNA")
        member_id: Member/Cardholder ID (e.g. "AET12345")
        group_number: Group number (e.g. "GRP100")

    Returns:
        bool: True if insurance was successfully added
    """
    try:
        desktop = Desktop(backend="uia")
        edit_window = desktop.window(title_re=config.SELECTOR_EDIT_PATIENT)

        grid = edit_window.child_window(auto_id="uxPayMethodsGrid", control_type="Table")
        grid.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("{F2}")
        time.sleep(1)

        send_keys(payer_name, with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{ENTER}")
        time.sleep(1)
        send_keys("{ENTER}")
        time.sleep(1)

        # Pay Method window should appear
        pay_window = edit_window.child_window(title_re=".*Pay Method.*", control_type="Window")
        pay_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        # Click Start hyperlink to enable fields
        try:
            start_link = pay_window.child_window(control_type="Hyperlink")
            start_link.click_input()
            time.sleep(config.TIMEOUT_AFTER_CLICK)
        except Exception:
            log_print("[INSURANCE] No Start hyperlink found — fields may already be editable")

        # Fill Cardholder ID (Member ID) if provided
        if member_id:
            try:
                cardholder_field = pay_window.child_window(auto_id="uxCardHolderId", control_type="Edit")
                cardholder_field.click_input()
                time.sleep(0.1)
                send_keys("^a{DELETE}")
                send_keys(member_id, with_spaces=True)
                time.sleep(config.TIMEOUT_AFTER_TYPE)
                send_keys("{TAB}")
                time.sleep(config.TIMEOUT_AFTER_CLICK)
                log_print(f"[INSURANCE] Member ID set: {member_id}")
            except Exception as e:
                log_print(f"[INSURANCE] Could not set Member ID: {e}")

        # Fill Group Number if provided
        if group_number:
            try:
                group_field = pay_window.child_window(auto_id="uxGroupNumber", control_type="Edit")
                group_field.click_input()
                time.sleep(0.1)
                send_keys("^a{DELETE}")
                send_keys(group_number, with_spaces=True)
                time.sleep(config.TIMEOUT_AFTER_TYPE)
                send_keys("{TAB}")
                time.sleep(config.TIMEOUT_AFTER_CLICK)
                log_print(f"[INSURANCE] Group Number set: {group_number}")
            except Exception as e:
                log_print(f"[INSURANCE] Could not set Group Number: {e}")

        # Fill BIN if provided
        if bin_number:
            try:
                bin_field = pay_window.child_window(auto_id="uxBin", control_type="Edit")
                bin_field.click_input()
                time.sleep(0.1)
                send_keys("^a{DELETE}")
                send_keys(bin_number, with_spaces=True)
                time.sleep(config.TIMEOUT_AFTER_TYPE)
                send_keys("{TAB}")
                time.sleep(config.TIMEOUT_AFTER_CLICK)
                log_print(f"[INSURANCE] BIN set: {bin_number}")
            except Exception as e:
                log_print(f"[INSURANCE] Could not set BIN: {e}")

        # Fill PCN if provided
        if pcn:
            try:
                pcn_field = pay_window.child_window(auto_id="uxPcn", control_type="Edit")
                pcn_field.click_input()
                time.sleep(0.1)
                send_keys("^a{DELETE}")
                send_keys(pcn, with_spaces=True)
                time.sleep(config.TIMEOUT_AFTER_TYPE)
                send_keys("{TAB}")
                time.sleep(config.TIMEOUT_AFTER_CLICK)
                log_print(f"[INSURANCE] PCN set: {pcn}")
            except Exception as e:
                log_print(f"[INSURANCE] Could not set PCN: {e}")

        # Set Billing Order to "Other"
        try:
            billing_combo = pay_window.child_window(title="Billing Order:", control_type="ComboBox")
            billing_edit = billing_combo.child_window(auto_id="1001", control_type="Edit")
            billing_edit.click_input()
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys("Other", with_spaces=True)
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys("{TAB}")
            time.sleep(config.TIMEOUT_AFTER_CLICK)
        except Exception as e:
            log_print(f"[INSURANCE] Could not set Billing Order: {e}")

        # Save pay method
        save_btn = pay_window.child_window(auto_id="uxSave", control_type="Button")
        save_btn.click_input()
        time.sleep(1)

        log_print(f"[INSURANCE] Insurance '{payer_name}' added successfully")
        return True

    except Exception as e:
        log_print(f"[INSURANCE] Failed to add insurance: {e}")
        return False


def close_edit_patient(save=True):
    """
    Close the Edit Patient window.

    Args:
        save: If True, clicks Save & Close. If False, presses ESC to cancel.

    Returns:
        bool: True if closed successfully
    """
    try:
        desktop = Desktop(backend="uia")
        edit_window = desktop.window(title_re=config.SELECTOR_EDIT_PATIENT)

        if save:
            for desc in edit_window.descendants():
                try:
                    props = desc.legacy_properties()
                    if props.get('Name') == 'Save & Close - F12' and props.get('Role') == 43:
                        desc.click_input()
                        time.sleep(0.5)
                        log_print("[INSURANCE] Edit Patient — Save & Close clicked")
                        return True
                except Exception:
                    continue
            log_print("[INSURANCE] Save & Close button not found — trying ESC")
            send_keys("{ESC}")
            time.sleep(0.5)
            return True
        else:
            send_keys("{ESC}")
            time.sleep(0.5)
            log_print("[INSURANCE] Edit Patient closed (no changes)")
            return True

    except Exception as e:
        log_print(f"[INSURANCE] Failed to close Edit Patient: {e}")
        send_keys("{ESC}")
        time.sleep(0.5)
        return False


def check_and_add_insurance(insurance_data):
    """
    Main workflow: Edit Patient -> check if insurance exists -> add if missing -> close.

    Args:
        insurance_data: dict with keys: payer, member_id, group_number, bin, pcn

    Returns:
        bool: True if insurance is present (already existed or successfully added)
    """
    payer = insurance_data.get("payer", "")
    if not payer:
        log_print("[INSURANCE] No payer name in insurance data — skipping")
        return False

    if not click_edit_patient():
        return False

    if has_insurance(payer):
        close_edit_patient(save=False)
        return True

    success = add_insurance_to_grid(
        payer_name=payer,
        bin_number=insurance_data.get("bin", ""),
        pcn=insurance_data.get("pcn", ""),
        member_id=insurance_data.get("member_id", ""),
        group_number=insurance_data.get("group_number", ""),
    )

    if success:
        close_edit_patient(save=True)
        return True
    else:
        close_edit_patient(save=False)
        return False


if __name__ == "__main__":
    test_insurance = {
        "payer": "Aetna",
        "member_id": "AET12345",
        "group_number": "GRP100",
        "bin": "610502",
        "pcn": "AETNA"
    }
    if check_and_add_insurance(test_insurance):
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
