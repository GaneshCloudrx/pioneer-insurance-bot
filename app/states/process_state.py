"""
Process State - Pioneer Insurance Bot
Orchestrates the insurance check/add workflow for all prescriptions of a patient.

Flow:
1. Extract all Rx numbers from the API response.
2. Search first Rx number in Rx Profile and open it.
3. **Pre-check on the Dispense tab**: if the Primary insurance combo already
   contains the API's cardholder digits, the patient is already configured —
   cancel the Rx, post `pms_synced`, and skip all remaining Rx numbers.
4. Otherwise open Edit Patient (pencil icon) and either find the matching
   insurance row (extract its payer name) or add a new one via the binocular
   search (extract the Pay Method window's Display Name).
5. Back on the Dispense tab, set the Primary combo to that insurance using
   `(P)<first word of display name>` + Tab when it isn't already selected.
6. Save & Continue, walking through all post-save popups (with recovery for
   third-party-setup and DAW errors).
7. For subsequent Rx numbers: repeat steps 5–6 using the same captured
   insurance name (no Edit Patient round-trip needed).
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
    select_rph,
    save_and_continue,
    error_and_warning,
    equivalent_rx,
    cancel_prescription,
    popup_handlers,
    dispense,
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


def _notify_failed(cld_patient_id, reason):
    """Best-effort 'failed' status update to the portal."""
    if cld_patient_id is None:
        return
    try:
        insurance_api.update_status(cld_patient_id, "failed")
        log_print(f"[PROCESS] Posted 'failed' to API ({reason}) — cld_patient_id={cld_patient_id}")
    except Exception as e:
        log_print(f"[PROCESS] Failed to post 'failed' to API: {e}")


def _save_and_handle_popups(rx_label, cld_patient_id):
    """
    Click Save & Continue and walk through all post-save popups, mirroring the
    CloudRx DE bot pattern:

        1. Save & Continue
        2. Equivalent Rx popup -> Fill Anyway
        3. Error / Warning List
             - If non-bypassable AND the error mentions
               "third party setup for primary claim submission only" OR "daw":
                   * Clear Secondary insurance / toggle DAW checkbox as needed
                   * Save & Continue again
                   * Equivalent Rx popup -> Fill Anyway
                   * Error / Warning List again
                   * If still non-bypassable: screenshot + cancel +
                     update API "failed" -> return False
             - If non-bypassable and not recoverable:
                   screenshot + cancel + update API "failed" -> return False
        4. Alerts popup (optional, captcha-aware)
        5. Equivalent Pending Rx popup -> Ignore and Continue

    Args:
        rx_label: Short label used in screenshot filenames and logs
                  (e.g. "first_rx_1448269").
        cld_patient_id: Optional cld_patient_id used to post a "failed"
                  status to the portal when the prescription is skipped.

    Returns:
        bool: True if Save & Continue completed cleanly (with or without
              recoverable warnings). False if the prescription had to be
              cancelled due to a non-bypassable error.
    """
    take_screenshot(f"before_save_{rx_label}")
    if not save_and_continue.click_save_and_continue():
        raise config.SystemException(f"Failed to save Rx {rx_label}")

    # Step 1: Equivalent Rx popup
    equivalent_rx.click_fill_anyway()

    # Step 2: Error / Warning List
    ew_success, non_bypassable, error_text = error_and_warning.handle_error_warning()
    if not ew_success and non_bypassable:
        error_lower = (error_text or "").lower()
        has_third_party = "third party setup for primary claim submission only" in error_lower
        has_daw = "daw" in error_lower

        if has_third_party or has_daw:
            if has_third_party:
                log_print("[PROCESS] Third Party error — setting Secondary to <None>")
                dispense.clear_secondary_insurance()
            if has_daw:
                log_print("[PROCESS] DAW error — toggling DAW checkbox")
                dispense.toggle_daw()

            if not save_and_continue.click_save_and_continue():
                raise config.SystemException(
                    f"Failed to re-save Rx {rx_label} after error fix"
                )

            equivalent_rx.click_fill_anyway()
            ew_success2, non_bypassable2, _ = error_and_warning.handle_error_warning()
            if not ew_success2 and non_bypassable2:
                take_screenshot("non_bypassable_error_after_fix")
                cancel_prescription.click_cancel()
                _notify_failed(cld_patient_id, "Non-bypassable error after fix")
                log_print(
                    f"[PROCESS] Non-bypassable error on Rx {rx_label} after fix — skipped"
                )
                return False
        else:
            take_screenshot("non_bypassable_error")
            cancel_prescription.click_cancel()
            _notify_failed(cld_patient_id, "Non-bypassable error")
            log_print(
                f"[PROCESS] Non-bypassable error on Rx {rx_label} ({error_text}) — skipped"
            )
            return False

    # Step 3: Alerts popup (captcha-aware, optional)
    error_and_warning.handle_alerts_popup()

    # Step 4: Equivalent Pending Rx popup
    equivalent_rx.click_ignore_and_continue()

    return True


def _process_first_rx(rx_number, insurance_data, cld_patient_id):
    """
    Process the first Rx number:
      1. Search and open the Rx, handle Priority/other popups.
      2. **Pre-check the Dispense Primary combo** — if it already contains
         the API cardholder digits the patient is already configured: cancel
         the Rx, post `pms_synced`, and tell the caller to skip every
         remaining Rx for this patient.
      3. Open Edit Patient, find the matching row (capture its payer name)
         or add a new plan via binocular search (capture the Pay Method
         window's Display Name).
      4. Back on the Edit Rx window, set the Primary combo on the Dispense
         tab using `(P)<first word of insurance name>` when it isn't
         already set.
      5. Select the RPh, then Save & Continue with the post-save recovery
         flow.

    Args:
        rx_number: The first Rx number to process.
        insurance_data: dict with payer, card_holder_id, group_number,
            bin, pcn — the active insurance from the API.
        cld_patient_id: Optional cld_patient_id from the API; used to post
            status updates.

    Returns:
        tuple(str, str):
            * status         - "completed" (Rx saved) or "already_synced"
              (Primary on Dispense already matched; remaining Rx skipped).
            * insurance_name - Display/payer name captured during the
              insurance step. Used by subsequent Rx so they can select
              the same plan as Primary. Empty string when no Edit Patient
              round-trip happened (already_synced).

    Raises:
        config.BusinessRuleException: Rx not found, insurance plan not
            found, or non-bypassable save error.
        config.SystemException: UI interaction failure.
    """
    log_print(f"[PROCESS] Processing FIRST Rx: {rx_number} (verify/add insurance)")

    # Step 1: Search for the Rx number
    search_success, rx_found = rx_search.search_and_open_rx(rx_number)
    if not search_success:
        raise config.SystemException(f"Rx search failed for {rx_number}")
    if not rx_found:
        raise config.BusinessRuleException(f"Rx not found: {rx_number}")

    # Step 2: Handle Priority window that appears after Edit button
    time.sleep(1)
    app_cache.reset()
    popup_handlers.click_cancel_priority()
    time.sleep(0.5)
    popup_handlers.handle_all_popups()

    # Step 3: Pre-check — is the Primary insurance combo already on the
    # right plan? If so, this patient's insurance is fully configured in
    # Pioneer; just cancel the Rx without saving and skip all remaining Rx.
    app_cache.reset()
    card_holder_id = insurance_data.get("card_holder_id", "")
    if dispense.primary_member_id_matches(card_holder_id):
        log_print(
            "[PROCESS] Dispense Primary already shows this patient's member id — "
            "cancelling Rx without save and skipping remaining Rx"
        )
        cancel_prescription.click_cancel()
        insurance_api.update_status(cld_patient_id, "pms_synced")
        return "already_synced", ""

    # Step 4: Check / add insurance via Edit Patient.
    # check_and_add_insurance itself posts the API status (pms_synced when
    # found or added, failed when unable to add) so we don't double-notify.
    app_cache.reset()
    insurance_status, insurance_name = check_insurance.check_and_add_insurance(
        insurance_data, cld_patient_id=cld_patient_id
    )

    if insurance_status == check_insurance.INSURANCE_FAILED:
        log_print("[PROCESS] Insurance plan not found")
        cancel_prescription.click_cancel()
        raise config.BusinessRuleException(f"Insurance plan not found for Rx: {rx_number}")

    log_print(
        f"[PROCESS] Insurance step: {insurance_status} "
        f"(insurance_name='{insurance_name}')"
    )

    # Step 5: Handle any popups that appeared after Edit Patient closed
    popup_handlers.click_cancel_priority()

    # Step 6: Make sure the Primary combo on Dispense reflects this plan.
    # When the patient already had the row in the grid the Primary field
    # almost certainly isn't on it; when we just added it Pioneer sometimes
    # auto-populates Primary. select_primary_insurance is verify-first AND
    # verify-after — it returns False unless the cardholder digits actually
    # ended up in the combo. We refuse to save an Rx whose Primary couldn't
    # be confirmed.
    app_cache.reset()
    primary_ok = select_primary_insurance.select_primary_insurance(
        payer_name=insurance_data.get("payer", ""),
        bin_number=insurance_data.get("bin", ""),
        card_holder_id=card_holder_id,
        pcn=insurance_data.get("pcn", ""),
        insurance_name=insurance_name,
    )
    if not primary_ok:
        log_print(
            f"[PROCESS] Primary insurance verification failed on first Rx "
            f"{rx_number} — cancelling without save"
        )
        take_screenshot(f"primary_verify_failed_first_rx_{rx_number}")
        cancel_prescription.click_cancel()
        raise config.BusinessRuleException(
            f"Primary insurance not on target plan for first Rx {rx_number}"
        )

    # Step 7: Select RPh pharmacist before saving
    app_cache.reset()
    if not select_rph.select_rph():
        log_print("[PROCESS] Warning: RPh selection failed — continuing to save")

    # Step 8: Save & Continue + post-save popups (with recovery flow)
    app_cache.reset()
    if not _save_and_handle_popups(f"first_rx_{rx_number}", cld_patient_id):
        raise config.BusinessRuleException(
            f"Non-bypassable error on first Rx {rx_number} — skipped"
        )

    log_print(f"[PROCESS] First Rx {rx_number} processed successfully")
    return "completed", insurance_name


def _process_subsequent_rx(rx_number, insurance_data, cld_patient_id, insurance_name=""):
    """
    Process subsequent Rx numbers (not the first):
      1. Search and open the Rx
      2. Handle popups
      3. Ensure the Primary insurance combo on the Dispense tab matches the
         API plan. If the field is already on it (BIN + cardholder match)
         we leave it alone; otherwise we type
         "(P)<first word of insurance_name>" + Tab.
      4. Save & Continue + post-save popups (with recovery).

    Args:
        rx_number: The Rx number to process.
        insurance_data: dict with keys: payer, bin, pcn, card_holder_id,
            group_number — the active insurance from the API.
        cld_patient_id: Optional cld_patient_id from API.
        insurance_name: Display/payer name captured during the first Rx
            (from Edit Patient's grid match or the Pay Method window's
            Display Name). Drives the "(P)<first word>" shortcut so
            Pioneer picks the right primary when more than one is on file.

    Returns:
        bool: True if processed successfully.

    Raises:
        config.BusinessRuleException: Rx not found or non-bypassable save error.
        config.SystemException: UI interaction failure.
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

    # Step 3: Verify/select Primary insurance for this Rx — the same check
    # we ran on the first Rx. If we can't confirm the cardholder digits
    # actually ended up in the combo, we refuse to save this Rx (the bot
    # raises so the outer loop moves to the next one).
    app_cache.reset()
    primary_ok = select_primary_insurance.select_primary_insurance(
        payer_name=insurance_data.get("payer", ""),
        bin_number=insurance_data.get("bin", ""),
        card_holder_id=insurance_data.get("card_holder_id", ""),
        pcn=insurance_data.get("pcn", ""),
        insurance_name=insurance_name,
    )
    if not primary_ok:
        log_print(
            f"[PROCESS] Primary insurance verification failed on Rx "
            f"{rx_number} — cancelling without save"
        )
        take_screenshot(f"primary_verify_failed_rx_{rx_number}")
        cancel_prescription.click_cancel()
        raise config.BusinessRuleException(
            f"Primary insurance not on target plan for Rx {rx_number}"
        )

    # Step 4: Select RPh pharmacist before saving
    app_cache.reset()
    if not select_rph.select_rph():
        log_print("[PROCESS] Warning: RPh selection failed — continuing to save")

    # Step 5: Save & Continue + post-save popups (with recovery flow)
    app_cache.reset()
    if not _save_and_handle_popups(f"rx_{rx_number}", cld_patient_id):
        raise config.BusinessRuleException(
            f"Non-bypassable error on Rx {rx_number} — skipped"
        )

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
    insurance_data = record.get("insurance", {})
    prescriptions = record.get("prescriptions", [])
    cld_patient_id = record.get("cld_patient_id")

    # Use primary insurance if it has a payer, otherwise fall back to secondary
    insurance_primary = insurance_data.get("primary", {})
    insurance_secondary = insurance_data.get("secondary", {})

    if insurance_primary.get("payer", "").strip():
        active_insurance = insurance_primary
    elif insurance_secondary.get("payer", "").strip():
        active_insurance = insurance_secondary
        log_print("[PROCESS] Primary insurance empty — using secondary")
    else:
        raise config.BusinessRuleException("No valid insurance found (primary and secondary both empty)")

    patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
    payer_name = active_insurance.get("payer", "")
    rx_numbers = [p["rx_number"] for p in prescriptions if p.get("rx_number")]

    if not rx_numbers:
        raise config.SkipException("No Rx numbers found in API response")

    log_print("=" * 60)
    log_print(f"[PROCESS] Patient: {patient_name}")
    log_print(f"[PROCESS] Insurance: {payer_name}")
    log_print(f"[PROCESS] Rx Numbers ({len(rx_numbers)}): {rx_numbers}")
    log_print("=" * 60)

    _ensure_pioneer_foreground()

    # Process first Rx — verify/add insurance on patient profile and
    # capture the plan's display name for later Primary selection.
    first_rx = rx_numbers[0]
    try:
        first_rx_result, insurance_name = _process_first_rx(
            first_rx, active_insurance, cld_patient_id
        )
    except (config.BusinessRuleException, config.SystemException):
        raise
    except Exception as e:
        raise config.SystemException(f"Unexpected error processing first Rx {first_rx}: {e}")

    # If the Dispense Primary combo already matched this patient's member id,
    # the first Rx was cancelled without saving and `pms_synced` has been
    # posted. Nothing more to do for the remaining Rx numbers.
    if first_rx_result == "already_synced":
        remaining = len(rx_numbers) - 1
        log_print(
            f"[PROCESS] Primary insurance already configured for {patient_name} — "
            f"skipping {remaining} remaining Rx number(s)"
        )
        log_print(f"[PROCESS] Completed (no save) for {patient_name}")
        return

    log_print(f"[PROCESS] Using insurance_name='{insurance_name}' for subsequent Rx")

    # Process remaining Rx numbers — only select insurance in Primary field
    for rx_number in rx_numbers[1:]:
        try:
            _ensure_pioneer_foreground()
            _process_subsequent_rx(
                rx_number,
                active_insurance,
                cld_patient_id,
                insurance_name=insurance_name,
            )
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
