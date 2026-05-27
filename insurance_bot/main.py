"""
Pioneer Insurance Bot - Main Entry Point
REFramework State Machine: INIT -> GET_DATA -> PROCESS -> END

This bot:
1. Fetches patient insurance data from API (patient info + insurance + list of Rx numbers)
2. Searches the first Rx number in Pioneer's Rx Profile
3. Opens Edit Rx, then Edit Patient to check/add insurance if missing
4. For subsequent Rx numbers, selects the correct insurance in Primary field on Dispense tab
5. Saves each Rx and handles all post-save popups
"""
import os
import time
import ctypes

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
from modules.helper import (
    log_print, init_log_file, close_log_file,
    save_to_report, take_screenshot,
)
from states import init_state, get_data_state, process_state, end_state

# Prevent Windows from sleeping
ctypes.windll.kernel32.SetThreadExecutionState(
    0x80000000 | 0x00000001 | 0x00000002
)

# Logging setup
init_log_file()
log_print(f"[MAIN] Bot started — {config.BOT_NAME} on {config.MACHINE_NAME}")

os.makedirs(config.DATA_DIR, exist_ok=True)

# State Machine
state = "INIT"
retry_count = 0
patient_count = 0

success_count = 0
business_errors = []
system_errors = []

try:
    while True:
        if state == "INIT":
            try:
                init_state.run()
                state = "GET_DATA"
                retry_count = 0
            except config.SystemException as e:
                log_print(f"[MAIN] INIT failed: {e}")
                retry_count += 1
                if retry_count < config.MAX_SYSTEM_RETRIES:
                    log_print(f"[MAIN] Retrying INIT ({retry_count}/{config.MAX_SYSTEM_RETRIES})...")
                    time.sleep(10)
                    state = "INIT"
                else:
                    system_errors.append(str(e))
                    state = "END"

        elif state == "GET_DATA":
            try:
                record = get_data_state.run()
                if record is None:
                    log_print("[MAIN] No records — waiting 30s before retry")
                    time.sleep(30)
                    state = "GET_DATA"
                else:
                    patient_count += 1
                    state = "PROCESS"
            except config.SystemException as e:
                log_print(f"[MAIN] GET_DATA failed: {e}")
                retry_count += 1
                if retry_count < config.MAX_SYSTEM_RETRIES:
                    state = "INIT"
                else:
                    system_errors.append(str(e))
                    state = "END"

        elif state == "PROCESS":
            try:
                process_state.run(record)

                patient = record.get("patient", {})
                report_data = {
                    "patient_id": patient.get("patient_id", ""),
                    "first_name": patient.get("first_name", ""),
                    "last_name": patient.get("last_name", ""),
                    "current_rx": ", ".join(p["rx_number"] for p in record.get("prescriptions", []) if p.get("rx_number")),
                    "payer": record.get("insurance", {}).get("payer", ""),
                }
                save_to_report(report_data, "Success", "Insurance processed for all Rx numbers")
                success_count += 1

                # Update API with success
                from modules import insurance_api
                insurance_api.update_status(
                    patient.get("patient_id", ""),
                    "success",
                    "Insurance verified/added successfully"
                )

                state = "GET_DATA"
                retry_count = 0

            except config.BusinessRuleException as e:
                patient = record.get("patient", {})
                patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
                log_print(f"[MAIN] Business error: {e}")

                report_data = {
                    "patient_id": patient.get("patient_id", ""),
                    "first_name": patient.get("first_name", ""),
                    "last_name": patient.get("last_name", ""),
                    "current_rx": "",
                    "payer": record.get("insurance", {}).get("payer", ""),
                }
                save_to_report(report_data, "Skipped", str(e))
                business_errors.append((patient_name, str(e)))

                from modules import insurance_api
                insurance_api.update_status(
                    patient.get("patient_id", ""), "skipped", str(e)
                )

                state = "GET_DATA"

            except config.SystemException as e:
                log_print(f"[MAIN] System error: {e}")
                take_screenshot("system_error")

                patient = record.get("patient", {})
                report_data = {
                    "patient_id": patient.get("patient_id", ""),
                    "first_name": patient.get("first_name", ""),
                    "last_name": patient.get("last_name", ""),
                    "current_rx": "",
                    "payer": record.get("insurance", {}).get("payer", ""),
                }
                save_to_report(report_data, "Failed", str(e))
                system_errors.append(str(e))

                from modules import insurance_api
                insurance_api.update_status(
                    patient.get("patient_id", ""), "failed", str(e)
                )

                retry_count += 1
                if retry_count < config.MAX_SYSTEM_RETRIES:
                    state = "INIT"
                else:
                    state = "END"

        elif state == "END":
            end_state.run(patient_count, success_count, business_errors, system_errors)
            log_print("[MAIN] Resetting for next cycle (24/7 mode)")
            state = "INIT"
            retry_count = 0
            patient_count = 0
            success_count = 0
            business_errors = []
            system_errors = []

except KeyboardInterrupt:
    log_print("[MAIN] Stopped by user")
    end_state.run(patient_count, success_count, business_errors, system_errors)
finally:
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    close_log_file()
    print("[MAIN] Cleanup complete")
