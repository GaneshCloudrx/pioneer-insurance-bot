"""
Process State - Orchestrate all modules for one prescription
Raises BusinessRuleException for expected errors, SystemException for unexpected
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.helper import log_print, take_screenshot


def _add_to_retry(unique_string):
    os.makedirs(os.path.dirname(config.RETRY_FILE_PATH), exist_ok=True)
    with open(config.RETRY_FILE_PATH, 'a') as f:
        f.write(unique_string + "\n")
from modules import (
    noactiveitem_, patient_filter, reminder, row_selection, process,
    priority_window_handle_popup, wizard_add_patient_popup,
    converted_data_popup, rxinuse_popup, renewable_request,
    xml_extraction, xml_api,
    patient_profile, search_patient, adding_patient,
    duplicate_patient,
    prescriber_profile, search_prescriber, adding_prescriber,
    duplicate_prescriber,
    drugtype_selection, search_drug, search_compound,
    drug_quantity, drug_unit, drug_sig,
    dispense, dispense_priority,
    e1lookup, cancel_prescription, update_api,
    save_and_continue, error_and_warning, critical_warning
)


def _handle_popups():
    """Dismiss any popups that may appear after opening an Rx."""
    for handler in [
        priority_window_handle_popup.click_cancel_priority,
        wizard_add_patient_popup.dismiss_wizard_popup,
        converted_data_popup.click_ok_conversion,
        rxinuse_popup.click_cancel_rxinuse,
        renewable_request.click_cancel_renew,
    ]:
        try:
            handler()
        except Exception:
            pass


def run(transaction, api_response):
    """
    Process a single prescription transaction.

    Args:
        transaction: dict with keys (index, unique_string, api_id, patient_name, priority)
        api_response: dict from XML API with all Rx field data

    Raises:
        config.BusinessRuleException: Patient/Drug not found, NON-MATCHED, etc.
        config.SystemException: App crash, timeout, element not found
    """
    log_print("=" * 60)
    log_print(f"[PROCESS] Processing: {transaction['patient_name']} | API ID: {transaction['api_id']}")
    log_print("=" * 60)

    # Tracks state for update_api calls — only valid after xml_api responds
    message_id = None
    update_sent = False
    new_patient_added = False
    e1_looked_up = False

    try:
        # ---- Step 0: Filter by patient ----
        if not patient_filter.filter_by_patient(transaction["patient_name"]):
            raise config.BusinessRuleException("Failed to filter by patient")

        # ---- Step 1: Select row in Fill Requests ----
        if not row_selection.select_row(transaction["index"]):
            _add_to_retry(transaction["unique_string"])
            raise config.BusinessRuleException("Failed to select row")

        # ---- Step 2: Click Process to open Rx ----
        if not process.click_process():
            raise config.SystemException("Failed to click Process")

        # ---- Step 3: Handle popups serially ----
        # Rx In Use: if found, cancel and skip to next queue record
        if rxinuse_popup.click_cancel_rxinuse():
            log_print("[PROCESS] Rx In Use — skipping to next record")
            raise config.BusinessRuleException("Rx is in use by another user")
        if renewable_request.click_cancel_renew():
            log_print("[PROCESS] Renewable Request — skipping to next record")
            raise config.BusinessRuleException("Rx is renewable")
        
        try:
            wizard_add_patient_popup.dismiss_wizard_popup()
        except Exception:
            pass

        

        try:
            priority_window_handle_popup.click_cancel_priority()
        except Exception:
            pass

        try:
            noactiveitem_.click_ok_noactiveitem()
        except Exception:
            pass
        

        # ---- Step 4: Extract XML & submit to API ----
        success, xml_data = xml_extraction.extract_xml()
        if not success or not xml_data:
            raise config.SystemException("Failed to extract XML")

        success, api_resp = xml_api.submit_xml(transaction["api_id"], xml_data)
        if not success or not api_resp:
            raise config.BusinessRuleException("API rejected XML submission")

        data = api_resp.get("data", {})
        message_id = data.get("message_id", "")
        transferred = data.get("transferred_drug", {}) or {}


        prescriber_data = data.get("prescriber", {}) or {}

        transaction["message_id"] = message_id
        transaction["prescriber_name"] = f"{prescriber_data.get('last_name', '')}, {prescriber_data.get('first_name', '')}".strip(", ")
        transaction["drug_name"] = transferred.get("transferred_drug", "") or ""
        transaction["ndc"] = (transferred.get("transferred_NDC", "") or "") if data.get("transferrable", 0) else ""
        transaction["patient_dob"] = (data.get("patient", {}) or {}).get("dob", "") or ""
        transaction["api_response"] = str(api_resp)

        #Check if transferrable status is 0

        if not data.get("transferrable", 0):
            update_api.update_skipped(message_id, "Transferrable status is 0")
            update_sent = True
            raise config.BusinessRuleException("Transferrable status is 0 — skipping Rx")

        # ---- Step 5: Patient ----
        patient_data = data.get("patient", {}) or {}
        patient_first = patient_data.get("first_name", "")
        patient_last = patient_data.get("last_name", "")

        # Parse DOB "YYYY-MM-DD" → month, day, year
        dob_raw = patient_data.get("dob", "") or ""
        dob_parts = dob_raw.split("-") if dob_raw else []
        dob_month = dob_parts[1] if len(dob_parts) == 3 else ""
        dob_day = dob_parts[2] if len(dob_parts) == 3 else ""
        dob_year = dob_parts[0] if len(dob_parts) == 3 else ""

        # Parse phone "8014035607" → area, prefix, suffix
        phone_raw = (patient_data.get("phone", "") or "").replace("-", "").replace(" ", "")
        phone_area = phone_raw[:3] if len(phone_raw) >= 10 else ""
        phone_prefix = phone_raw[3:6] if len(phone_raw) >= 10 else ""
        phone_suffix = phone_raw[6:10] if len(phone_raw) >= 10 else ""

        category = data.get("category", "") or "" 
        patient_found = patient_profile.check_patient_name(patient_first.split(" ")[0].split("-")[0])

        if not patient_found:
            search_patient.click_search()
            pat_success, is_new = search_patient.search_and_select_patient(
                patient_first, patient_last,
                dob_month, dob_day, dob_year,
                phone_area, phone_prefix, phone_suffix
            )
            if not pat_success:
                raise config.SystemException("Patient search failed")

            if is_new:
                adding_patient.click_add_patient()
                adding_patient.set_patient_notification()
                adding_patient.click_categories_tab(category)
                adding_patient.click_save_and_close()
                if duplicate_patient.click_cancel_duplicate():
                    adding_patient.click_cancel()
                    search_patient.click_search()
                    pat_success, is_new = search_patient.search_and_select_patient(
                        patient_first, patient_last,
                        dob_month, dob_day, dob_year,
                        phone_area, phone_prefix, phone_suffix
                    )
                    if not pat_success or is_new:
                        _add_to_retry(transaction["unique_string"])
                        update_api.update_skipped(message_id, "Patient not found")
                        update_sent = True
                        raise config.BusinessRuleException("Patient not found after duplicate check")
                else:
                    new_patient_added = True
                

        # ---- Step 5.1: Handle Critical Warning captcha ----
        if not critical_warning.handle_critical_warning():
            raise config.SystemException("Failed to handle critical warning captcha")
        
        # ---- Step 5.2: handle priority window if appears ----
        if priority_window_handle_popup.click_cancel_priority():
            log_print("[PROCESS] Priority window not found")
        else:
            log_print("[PROCESS] Priority window not found")

        # ---- Step 6: Prescriber ----
        presc_last = prescriber_data.get("last_name", "")
        presc_found = prescriber_profile.check_prescriber_name(presc_last)

        if not presc_found:
            search_prescriber.click_search()
            presc_success, is_new = search_prescriber.search_and_select_prescriber(
                prescriber_data.get("NPI", ""),
                prescriber_data.get("address_state", ""),
                prescriber_data.get("address_postal_code", "")
            )
            if not presc_success:
                raise config.SystemException("Prescriber search failed")

            if is_new:
                adding_prescriber.click_add_prescriber()
                adding_prescriber.set_prescriber_type("M.D.")
                adding_prescriber.click_save_and_close()
                if duplicate_prescriber.click_no_duplicate():
                    adding_prescriber.click_cancel()
                    search_prescriber.click_search()
                    presc_success, is_new = search_prescriber.search_and_select_prescriber(
                        prescriber_data.get("NPI", ""),
                        prescriber_data.get("address_state", ""),
                        prescriber_data.get("address_postal_code", "")
                    )
                    if not presc_success or is_new:
                        _add_to_retry(transaction["unique_string"])
                        update_api.update_skipped(message_id, "Prescriber not found")
                        update_sent = True
                        raise config.BusinessRuleException("Prescriber not found after duplicate check")

        
        # ---- Step 7: Drug Type & Search ----
        is_compound = bool(transferred.get("compound", 0))
        drugtype_selection.select_drug_type(is_compound=is_compound)

        ndc = (transferred.get("transferred_NDC") or "").strip()
        if not ndc or not ndc.replace("-", "").isdigit():
            update_api.update_skipped(message_id, f"Invalid NDC number: {ndc}")
            update_sent = True
            raise config.BusinessRuleException(f"Invalid NDC number: {ndc}")

        if is_compound:
            drug_success, drug_found = search_compound.search_compound(ndc)
        else:
            drug_success, drug_found = search_drug.search_drug(ndc)

        if not drug_success:
            raise config.SystemException("Drug search failed")
        if not drug_found:
            _add_to_retry(transaction["unique_string"])
            update_api.update_skipped(message_id, f"Drug not found: NDC {ndc}")
            update_sent = True
            raise config.BusinessRuleException(f"Drug not found: NDC {ndc}")

        # ---- Step 8: Fill Rx fields (from transferred_drug) ----
        quantity = transferred.get("transferred_qty", "") or ""
        if quantity:
            log_print(f"[PROCESS] Setting quantity: {quantity}")
            drug_quantity.set_quantity(quantity)

        unit = transferred.get("transferred_unit", "") or ""
        if unit:
            log_print(f"[PROCESS] Setting unit: {unit}")
            drug_unit.set_unit(unit)

        sig = transferred.get("transferred_sig", "") or ""
        if sig:
            drug_sig.set_sig(sig)

        # ---- Step 9: Dispense ----
        disp_qty = quantity
        days = transferred.get("transferred_ds", "") or ""
        if disp_qty or days:
            log_print(f"[PROCESS] Setting dispense: {disp_qty}, {days}")
            dispense.set_dispense(disp_qty, days, "Abigail")

        # ---- Step 10: Priority ----
        api_priority = data.get("priority", transaction.get("priority", ""))
        if api_priority:
            dispense_priority.check_priority(api_priority)

        # ---- Step 11: E1 Lookup ----
        # This steps only for new patients
        if new_patient_added:
            e1_success, e1_matched = e1lookup.e1_lookup()
            if e1_success:
                log_print("[PROCESS] E1 LOOKUP SUCCESSFUL")
                e1_looked_up = True
            else:
                raise config.SystemException("E1 lookup failed")

        # ---- Step 12: Save & Continue ----
        take_screenshot("before_save")
        if not save_and_continue.click_save_and_continue():
            raise config.SystemException("Failed to save and continue")

        

        # ---- Step 14: Handle Error/Warning List ----
        ew_success, non_bypassable = error_and_warning.handle_error_warning()
        if not ew_success and non_bypassable:
            cancel_prescription.click_cancel()
            update_api.update_skipped(message_id, "Non-bypassable error")
            update_sent = True
            raise config.BusinessRuleException("Non-bypassable error — prescription skipped")

        # ---- Step 14.1: Handle Alerts popup (optional) ----
        error_and_warning.handle_alerts_popup()

        # ---- Step 15: Update API — success ----
        update_api.update_success(
            message_id,
            e1_look_up="1" if e1_looked_up else "0",
            new_patient_in_pioneer="1" if new_patient_added else "0"
        )
        update_sent = True

        log_print(f"[PROCESS] Completed: {transaction['patient_name']}")

    except config.BusinessRuleException:
        cancel_prescription.click_cancel()
        if message_id and not update_sent:
            update_api.update_failed(message_id, "Business rule exception")
        raise
    except config.SystemException as exc:
        take_screenshot("system_error")
        cancel_prescription.click_cancel()
        if message_id and not update_sent:
            update_api.update_failed(message_id, str(exc))
        raise
    except Exception as exc:
        take_screenshot("system_error")
        cancel_prescription.click_cancel()
        if message_id and not update_sent:
            update_api.update_failed(message_id, str(exc))
        raise config.SystemException(f"Unexpected error in process: {exc}")
