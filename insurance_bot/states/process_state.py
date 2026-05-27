"""
Process State - Pioneer Insurance Bot
Orchestrates the insurance check/add workflow for all prescriptions of a patient.

Flow:
1. Extract all Rx numbers from the API response
2. Search first Rx number in Rx Profile (like Prescription Automation Bot)
3. Click Edit to open Edit Rx
4. Open Edit Patient (pencil icon) and check/add insurance (first Rx only)
5. For subsequent Rx numbers: select correct insurance in Primary textbox on Dispense tab
6. Save and handle popups after each Rx
"""
import sys, os
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print, take_screenshot, force_foreground, ensure_session_active
from modules import (
    app_cache,
    rx_search,
    check_insurance,
    select_primary_insurance,
    save_and_continue,
    error_and_warning,
    cancel_prescription,
    popup_handlers,
    insurance_api,
)


def _ensure_pioneer_foreground():
    """Bring Pioneer to foreground before UI interaction."""
    try:
        app = Application(backend="uia").connect(
            title_re=config.SELECTOR_FILL_REQUESTS,
            timeout=config.TIMEOUT_ELEMENT_VISIBLE,
        )
        window = app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        force_foreground(window.handle)
        ensure_session_active()
    except Exception as e:
        log_print(f"[PROCESS] Focus recovery warning: {e}")


def _handle_post_save_popups():
    """
    Handle all popups that may appear after Save & Continue.
    Same pattern as CloudRx DE bot.
    """
    # Handle Equivalent Rx popup
    error_and_warning.handle_equivalent_rx()

    # Handle Error/Warning List
    ew_success, non_bypassable = error_and_warning.handle_error_warning()
    if not ew_success and non_bypassable:
        log_print("[PROCESS] Non-bypassable error detected")
        return False

    # Handle Alerts popup
    error_and_warning.handle_alerts_popup()

    # Handle Equivalent Pending Rx popup
    error_and_warning.handle_equivalent_pending()

    return True


def _process_first_rx(rx_number, insurance_data):
    """
    Process the first Rx number:
    1. Search and open the Rx
    2. Handle popups
    3. Open Edit Patient and check/add insurance
    4. Save & Continue
    5. Handle post-save popups

    Args:
        rx_number: The first Rx number to process
        insurance_data: dict with payer, member_id, group_number, bin, pcn

    Returns:
        bool: True if processed successfully

    Raises:
        config.BusinessRuleException: If Rx not found
        config.SystemException: If UI interaction fails
    """
    log_print(f"[PROCESS] Processing FIRST Rx: {rx_number} (add insurance)")

    # Step 1: Search for the Rx number
    search_success, rx_found = rx_search.search_and_open_rx(rx_number)
    if not search_success:
        raise config.SystemException(f"Rx search failed for {rx_number}")
    if not rx_found:
        raise config.BusinessRuleException(f"Rx not found: {rx_number}")

    # Step 2: Handle popups that may appear after opening Rx
    time.sleep(0.5)
    popup_handlers.handle_all_popups()

    # Step 3: Check and add insurance via Edit Patient
    app_cache.reset()
    insurance_added = check_insurance.check_and_add_insurance(insurance_data)
    if not insurance_added:
        log_print("[PROCESS] Insurance check/add failed — continuing with save")

    # Step 4: Handle any popups that appeared after Edit Patient closed
    popup_handlers.click_cancel_priority()

    # Step 5: Save & Continue
    app_cache.reset()
    take_screenshot("before_save_first_rx")

    if not save_and_continue.click_save_and_continue():
        raise config.SystemException("Failed to save first Rx")

    # Step 6: Handle post-save popups
    if not _handle_post_save_popups():
        cancel_prescription.click_cancel()
        raise config.BusinessRuleException("Non-bypassable error on first Rx — skipped")

    log_print(f"[PROCESS] First Rx {rx_number} processed successfully")
    return True


def _process_subsequent_rx(rx_number, payer_name):
    """
    Process subsequent Rx numbers (not the first):
    1. Search and open the Rx
    2. Handle popups
    3. Select correct insurance in Primary textbox on Dispense tab
    4. Save & Continue
    5. Handle post-save popups

    Args:
        rx_number: The Rx number to process
        payer_name: Insurance payer name to select in Primary field

    Returns:
        bool: True if processed successfully

    Raises:
        config.BusinessRuleException: If Rx not found
        config.SystemException: If UI interaction fails
    """
    log_print(f"[PROCESS] Processing subsequent Rx: {rx_number} (select insurance only)")

    # Step 1: Search for the Rx number
    search_success, rx_found = rx_search.search_and_open_rx(rx_number)
    if not search_success:
        raise config.SystemException(f"Rx search failed for {rx_number}")
    if not rx_found:
        raise config.BusinessRuleException(f"Rx not found: {rx_number}")

    # Step 2: Handle popups
    time.sleep(0.5)
    popup_handlers.handle_all_popups()

    # Step 3: Select the correct insurance in Primary textbox on Dispense tab
    app_cache.reset()
    select_primary_insurance.select_primary_insurance(payer_name)

    # Step 4: Save & Continue
    app_cache.reset()
    take_screenshot(f"before_save_rx_{rx_number}")

    if not save_and_continue.click_save_and_continue():
        raise config.SystemException(f"Failed to save Rx {rx_number}")

    # Step 5: Handle post-save popups
    if not _handle_post_save_popups():
        cancel_prescription.click_cancel()
        raise config.BusinessRuleException(f"Non-bypassable error on Rx {rx_number} — skipped")

    log_print(f"[PROCESS] Rx {rx_number} processed successfully")
    return True


def run(record):
    """
    Process all prescriptions for a patient:
    - First Rx: check/add insurance on patient profile
    - Subsequent Rx: only select insurance in Primary field on Dispense tab

    Args:
        record: API response dict with patient, insurance, prescriptions

    Raises:
        config.BusinessRuleException: For expected business errors
        config.SystemException: For unexpected system errors
    """
    app_cache.reset()

    patient = record.get("patient", {})
    insurance = record.get("insurance", {})
    prescriptions = record.get("prescriptions", [])

    patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
    payer_name = insurance.get("payer", "")
    rx_numbers = [p["rx_number"] for p in prescriptions if p.get("rx_number")]

    if not rx_numbers:
        raise config.BusinessRuleException("No Rx numbers found in API response")

    log_print("=" * 60)
    log_print(f"[PROCESS] Patient: {patient_name}")
    log_print(f"[PROCESS] Insurance: {payer_name}")
    log_print(f"[PROCESS] Rx Numbers ({len(rx_numbers)}): {rx_numbers}")
    log_print("=" * 60)

    _ensure_pioneer_foreground()

    # Process first Rx — add insurance to patient profile
    first_rx = rx_numbers[0]
    try:
        _process_first_rx(first_rx, insurance)
    except (config.BusinessRuleException, config.SystemException):
        raise
    except Exception as e:
        raise config.SystemException(f"Unexpected error processing first Rx {first_rx}: {e}")

    # Process remaining Rx numbers — only select insurance in Primary field
    for rx_number in rx_numbers[1:]:
        try:
            _ensure_pioneer_foreground()
            _process_subsequent_rx(rx_number, payer_name)
        except config.BusinessRuleException as e:
            log_print(f"[PROCESS] Business error on Rx {rx_number}: {e} — continuing to next")
            continue
        except config.SystemException as e:
            log_print(f"[PROCESS] System error on Rx {rx_number}: {e} — continuing to next")
            continue
        except Exception as e:
            log_print(f"[PROCESS] Unexpected error on Rx {rx_number}: {e} — continuing to next")
            continue

    log_print(f"[PROCESS] All {len(rx_numbers)} Rx numbers processed for {patient_name}")
