"""
Check and Add Insurance Module
Opens Edit Patient, checks if the target insurance exists in the pay methods grid,
and adds it if not present.

This is the core insurance logic — generalized to any insurance payer from the API response.
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
    Waits for the Edit Patient window to actually appear, handling any popups in between.

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

        # Verify Edit Patient window actually opened
        desktop = Desktop(backend="uia")
        edit_window = desktop.window(title_re=config.SELECTOR_EDIT_PATIENT)
        edit_window.wait('visible', timeout=3)
        log_print("[INSURANCE] Edit Patient window confirmed open")
        return True

    except Exception as e:
        log_print(f"[INSURANCE] Failed to click Edit Patient: {e}")
        return False


def has_insurance(card_holder_id):
    """
    Check if an insurance with the same Cardholder ID already exists in the
    patient's pay methods (third party insurance) grid.

    The API's card_holder_id may contain alphabetic characters (e.g. "ABC111513983").
    Only the numeric portion is used for comparison. Each cell value in the grid
    is also reduced to its digits, then matched as a substring so that a stored
    cardholder id is considered the same insurance regardless of any letter
    prefixes/suffixes either side may carry.

    Args:
        card_holder_id: Card Holder ID from the API response (may contain letters)

    Returns:
        bool: True if a row with a matching cardholder id already exists
    """
    if not card_holder_id:
        log_print("[INSURANCE] No cardholder ID provided — cannot check grid")
        return False

    numeric_id = "".join(ch for ch in str(card_holder_id) if ch.isdigit())
    if not numeric_id:
        log_print(f"[INSURANCE] Cardholder ID '{card_holder_id}' has no digits to match")
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
                    cell_numeric = "".join(ch for ch in val if ch.isdigit())
                    if cell_numeric and numeric_id in cell_numeric:
                        log_print(f"[INSURANCE] Cardholder ID '{numeric_id}' already exists in insurance grid")
                        return True
                except Exception:
                    pass

        log_print(f"[INSURANCE] Cardholder ID '{numeric_id}' not found in insurance grid")
        return False

    except Exception as e:
        log_print(f"[INSURANCE] Failed to check insurance grid: {e}")
        return False


def _is_pcn_blank(pcn):
    """Return True when the API's PCN should be treated as "no PCN"."""
    if pcn is None:
        return True
    cleaned = str(pcn).strip()
    if not cleaned:
        return True
    return cleaned.lower() in ("na", "n/a", "null", "none")


def _click_first_uxcancel(parent, label):
    """
    Click the first descendant Button whose AutomationId is 'uxCancel' inside
    the given parent. Falls back to {ESC} if no button is found.

    When more than one matches (e.g. the search dialog's Cancel and the parent
    window's Cancel are both descendants), the deepest/bottommost one (largest
    top coordinate) is clicked — the inner search Cancel sits below the Pay
    Method Cancel on screen, so this consistently targets the innermost open
    dialog first.

    Returns True if a uxCancel button was clicked.
    """
    try:
        if not parent.exists(timeout=1):
            return True  # Already closed
    except Exception:
        pass

    cancels = []
    try:
        for btn in parent.descendants(control_type="Button"):
            try:
                if btn.element_info.automation_id == "uxCancel":
                    cancels.append(btn)
            except Exception:
                continue
    except Exception as e:
        log_print(f"[INSURANCE] Error enumerating Cancel buttons on {label}: {e}")

    if not cancels:
        log_print(f"[INSURANCE] No uxCancel button found on {label} — pressing ESC")
        send_keys("{ESC}")
        time.sleep(0.5)
        return False

    try:
        chosen = max(cancels, key=lambda b: b.rectangle().top)
        chosen.click_input()
        log_print(f"[INSURANCE] Cancel clicked on {label}")
        time.sleep(0.5)
        return True
    except Exception as e:
        log_print(f"[INSURANCE] Failed to click Cancel on {label}: {e}")
        send_keys("{ESC}")
        time.sleep(0.5)
        return False


def _cancel_third_party_search(desktop):
    """Close the Third Party Search / Search For Third Party dialog."""
    for title_pattern in (".*Third Party Search.*", ".*Search For Third Party.*"):
        try:
            win = desktop.window(title_re=title_pattern)
            if win.exists(timeout=1):
                if _click_first_uxcancel(win, f"'{title_pattern}' window"):
                    return True
        except Exception:
            continue
    log_print("[INSURANCE] Third Party Search window not found — pressing ESC")
    send_keys("{ESC}")
    time.sleep(0.5)
    return False


def _cancel_pay_method(pay_window):
    """Close the Pay Method (Third Party) window via its Cancel button."""
    return _click_first_uxcancel(pay_window, "Pay Method (Third Party) window")


def _fill_search_field(field, value):
    """Click an Edit control, clear it, and type the given value."""
    field.click_input()
    time.sleep(0.1)
    send_keys("^a{DELETE}")
    send_keys(str(value), with_spaces=True)
    time.sleep(config.TIMEOUT_AFTER_TYPE)


def _get_cell_value(row, column_name):
    """
    Return the Value of the cell in `row` whose Name matches `column_name`
    (case-insensitive). Returns empty string if not found.
    """
    target = (column_name or "").strip().upper()
    for cell in row.children():
        try:
            name = (cell.window_text() or "").strip().upper()
            if name == target:
                return (cell.legacy_properties().get("Value", "") or "").strip()
        except Exception:
            continue
    return ""


def _select_search_result(search_window, prefer_row_without_pcn):
    """
    Pick the appropriate row from the ultraGrid1 results table and confirm it.

    When `prefer_row_without_pcn` is True, return the first row whose PCN cell
    Value is blank. Otherwise (or if no blank-PCN row exists) select the first
    row. Confirmation is done by double-clicking the row so the Pay Method
    window receives the selected plan.

    Returns True if a row was selected.
    """
    try:
        table = search_window.child_window(title="ultraGrid1", control_type="Table")
        table.wait('exists', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
    except Exception as e:
        log_print(f"[INSURANCE] Search results table 'ultraGrid1' not found: {e}")
        return False

    rows = []
    for child in table.children():
        try:
            if (child.window_text() or "").startswith("Table row"):
                rows.append(child)
        except Exception:
            continue

    if not rows:
        log_print("[INSURANCE] No rows in search results")
        return False

    log_print(f"[INSURANCE] {len(rows)} result row(s) returned")

    chosen = None
    if prefer_row_without_pcn:
        for row in rows:
            if not _get_cell_value(row, "PCN"):
                chosen = row
                log_print("[INSURANCE] Picked first result row with empty PCN")
                break
        if chosen is None:
            log_print("[INSURANCE] No row with empty PCN — falling back to first row")
            chosen = rows[0]
    else:
        chosen = rows[0]
        log_print("[INSURANCE] Picked first matching row")

    try:
        chosen.double_click_input()
    except Exception:
        try:
            chosen.click_input()
            send_keys("{ENTER}")
        except Exception as e:
            log_print(f"[INSURANCE] Failed to confirm selected row: {e}")
            return False

    time.sleep(1)
    return True


def _search_third_party_by_bin_pcn(search_window, bin_number, pcn, pcn_blank):
    """
    Fill BIN (and PCN when present), click Search (F12), then select the right
    result row. Returns True if a plan was selected.
    """
    try:
        bin_field = search_window.child_window(auto_id="uxBIN", control_type="Edit")
        bin_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        _fill_search_field(bin_field, bin_number)
        log_print(f"[INSURANCE] Search BIN set: {bin_number}")
    except Exception as e:
        log_print(f"[INSURANCE] Could not set BIN in search: {e}")
        return False

    if not pcn_blank:
        try:
            pcn_field = search_window.child_window(auto_id="uxPCN", control_type="Edit")
            pcn_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
            _fill_search_field(pcn_field, pcn)
            log_print(f"[INSURANCE] Search PCN set: {pcn}")
        except Exception as e:
            log_print(f"[INSURANCE] Could not set PCN in search: {e}")
    else:
        log_print("[INSURANCE] PCN is blank/na — searching by BIN only")

    try:
        search_btn = search_window.child_window(auto_id="uxSearch", control_type="Button")
        search_btn.click_input()
        log_print("[INSURANCE] Search (F12) button clicked")
    except Exception as e:
        log_print(f"[INSURANCE] Search button not found, pressing F12: {e}")
        send_keys("{F12}")

    time.sleep(config.TIMEOUT_AFTER_SEARCH)

    return _select_search_result(search_window, prefer_row_without_pcn=pcn_blank)


def add_insurance_to_grid(payer_name, bin_number="", pcn="", card_holder_id="", group_number=""):
    """
    Add a new insurance entry to the patient's pay methods grid using the
    advanced (binocular) search by BIN/PCN.

    Flow:
    1. Click pay methods grid and press F2 to start a new entry
    2. Pay Method (Third Party) window opens
    3. Click the binocular icon (AdvancedSearchButton) — Search For Third Party opens
    4. Type the BIN (and PCN when the API provided one)
    5. Trigger search; pick the first result row — or, when PCN was blank/na,
       the first row whose PCN column is empty
    6. Pay Method window is populated with the selected plan
    7. Fill Card Holder ID, Group Number, Billing Order and save

    Args:
        payer_name: Insurance payer name (kept for logging only)
        bin_number: BIN number used to drive the advanced search
        pcn: PCN value used to drive the advanced search ("na"/empty = skip)
        card_holder_id: Card Holder ID to fill in the Pay Method window
        group_number: Group number to fill in the Pay Method window

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

        # Pay Method window should appear
        pay_window = edit_window.child_window(title_re=".*Pay Method.*", control_type="Window")
        pay_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        # --- Advanced search via binocular icon ---
        pcn_blank = _is_pcn_blank(pcn)

        if not bin_number:
            log_print("[INSURANCE] No BIN provided — cannot perform advanced search")
            _cancel_pay_method(pay_window)
            return False

        try:
            # This version of pywinauto's descendants() doesn't accept `auto_id`
            # as a criteria kwarg, so collect all buttons and filter by the
            # AutomationId attribute manually.
            candidates = []
            for btn in pay_window.descendants(control_type="Button"):
                try:
                    if btn.element_info.automation_id == "AdvancedSearchButton":
                        candidates.append(btn)
                except Exception:
                    continue

            if not candidates:
                log_print("[INSURANCE] No AdvancedSearchButton found in Pay Method window")
                return False

            # Multiple binoculars exist in the Pay Method window (e.g. one for
            # the third-party plan and others for cardholder/prescriber lookups).
            # The third-party plan binocular is the topmost one on the form, so
            # pick the candidate with the smallest top coordinate.
            advanced_btn = min(candidates, key=lambda b: b.rectangle().top)
            advanced_btn.click_input()
            time.sleep(1)
            log_print(
                f"[INSURANCE] Binocular (advanced search) clicked "
                f"({len(candidates)} candidate(s), picked topmost)"
            )
        except Exception as e:
            log_print(f"[INSURANCE] Could not click binocular icon: {e}")
            return False

        search_window = desktop.window(title_re=".*Search For Third Party.*")
        try:
            search_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
            search_window.set_focus()
        except Exception as e:
            log_print(f"[INSURANCE] Search For Third Party window did not appear: {e}")
            return False

        selected = _search_third_party_by_bin_pcn(
            search_window, bin_number, pcn, pcn_blank
        )

        if not selected:
            log_print("[INSURANCE] No matching plan selected from advanced search")
            _cancel_third_party_search(desktop)
            _cancel_pay_method(pay_window)
            return False

        # Pay Method window should now be focused with the selected plan
        pay_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        # Click Start hyperlink to enable fields
        try:
            start_link = pay_window.child_window(control_type="Hyperlink")
            start_link.click_input()
            time.sleep(config.TIMEOUT_AFTER_CLICK)
        except Exception:
            log_print("[INSURANCE] No Start hyperlink found — fields may already be editable")

        # Fill Card Holder ID
        if card_holder_id:
            try:
                cardholder_field = pay_window.child_window(auto_id="uxCardholderID", control_type="Edit")
                cardholder_field.click_input()
                time.sleep(0.1)
                send_keys("{END}+{HOME}{DELETE}")
                send_keys(card_holder_id, with_spaces=True)
                time.sleep(config.TIMEOUT_AFTER_TYPE)
                send_keys("{TAB}")
                time.sleep(config.TIMEOUT_AFTER_CLICK)
                log_print(f"[INSURANCE] Card Holder ID set: {card_holder_id}")
            except Exception as e:
                log_print(f"[INSURANCE] Could not set Card Holder ID: {e}")

        # Fill Group Number
        if group_number:
            try:
                group_field = pay_window.child_window(auto_id="uxGroupNumber", control_type="Edit")
                group_field.click_input()
                time.sleep(0.1)
                send_keys("{END}+{HOME}{DELETE}")
                send_keys(group_number, with_spaces=True)
                time.sleep(config.TIMEOUT_AFTER_TYPE)
                send_keys("{TAB}")
                time.sleep(config.TIMEOUT_AFTER_CLICK)
                log_print(f"[INSURANCE] Group Number set: {group_number}")
            except Exception as e:
                log_print(f"[INSURANCE] Could not set Group Number: {e}")

        # Set Billing Order
        try:
            billing_combo = pay_window.child_window(title="Billing Order:", control_type="ComboBox")
            billing_edit = billing_combo.child_window(auto_id="1001", control_type="Edit")
            billing_edit.click_input()
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys("Primary", with_spaces=True)
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys("{TAB}")
            time.sleep(config.TIMEOUT_AFTER_CLICK)
        except Exception as e:
            log_print(f"[INSURANCE] Could not set Billing Order: {e}")

        # Save pay method
        save_btn = pay_window.child_window(auto_id="uxSave", control_type="Button")
        save_btn.click_input()
        time.sleep(1)

        # Check if Error Warning List popup appeared (insurance plan not found)
        try:
            error_win = pay_window.child_window(title="Error  Warning List", control_type="Window")
            if error_win.exists(timeout=2):
                log_print("[INSURANCE] Insurance plan not found — Error Warning List appeared")
                close_btn = error_win.child_window(auto_id="uxClose", control_type="Button")
                close_btn.click_input()
                time.sleep(0.5)

                cancel_btn = pay_window.child_window(auto_id="uxCancel", control_type="Button")
                cancel_btn.click_input()
                time.sleep(0.5)
                log_print("[INSURANCE] Pay Method window cancelled")
                return False
        except Exception:
            pass

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


def _notify_api_failed(cld_patient_id):
    """Best-effort 'failed' status update; never raises."""
    if cld_patient_id is None:
        return
    try:
        from modules.insurance_api import update_status
        update_status(cld_patient_id, "failed")
    except Exception as e:
        log_print(f"[INSURANCE] Failed to send 'failed' status to API: {e}")


def check_and_add_insurance(insurance_data, cld_patient_id=None):
    """
    Main workflow: Edit Patient -> check if insurance exists -> add if missing -> close.

    When the insurance plan cannot be added (e.g. no matching plan in the
    advanced BIN/PCN search), all three windows are cancelled in order
    (Third Party Search -> Pay Method (Third Party) -> Edit Patient) and the
    portal is notified via `update_status(cld_patient_id, "failed")`.

    Args:
        insurance_data: dict with keys: payer, card_holder_id, group_number, bin, pcn
        cld_patient_id: Optional cld_patient_id from the API response. When
            provided, a 'failed' status update is sent if the plan cannot be
            added.

    Returns:
        bool: True if insurance is present (already existed or successfully added)
    """
    payer = insurance_data.get("payer", "")
    card_holder_id = insurance_data.get("card_holder_id", "")
    if not payer:
        log_print("[INSURANCE] No payer name in insurance data — skipping")
        return False

    if not click_edit_patient():
        _notify_api_failed(cld_patient_id)
        return False

    if has_insurance(card_holder_id):
        close_edit_patient(save=False)
        return True

    success = add_insurance_to_grid(
        payer_name=payer,
        bin_number=insurance_data.get("bin", ""),
        pcn=insurance_data.get("pcn", ""),
        card_holder_id=insurance_data.get("card_holder_id", ""),
        group_number=insurance_data.get("group_number", ""),
    )

    if success:
        close_edit_patient(save=True)
        return True
    else:
        close_edit_patient(save=False)
        _notify_api_failed(cld_patient_id)
        return False


if __name__ == "__main__":
    test_insurance = {
        "payer": "Cigna",
        "card_holder_id": "111513983",
        "group_number": "CIGUG0000658718",
        "bin": "017010",
        "pcn": "0518GWH"
    }
    if check_and_add_insurance(test_insurance):
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
