"""
Pioneer Data Entry Automation - REFramework State Machine
States: INIT -> GET_DATA -> PROCESS -> END
"""
import os
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
from modules.helper import (
    log_print, init_log_file, close_log_file,
    init_log_queue_manager, close_log_queue_manager,
    start_recording, stop_recording, cleanup_old_recordings,
    save_to_report,
)
from states import init_state, get_data_state, process_state, end_state

# ── Logging & Recording Setup ────────────────────────────────────────────────
init_log_file()
init_log_queue_manager()
cleanup_old_recordings()
start_recording()

log_print(f"[MAIN] Bot started — {config.BOT_NAME} on {config.MACHINE_NAME}")

# ── State Machine ────────────────────────────────────────────────────────────
state = "INIT"
retry_count = 0
transaction_number = 0
transaction = None

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
                system_errors.append(str(e))
                state = "END"

        elif state == "GET_DATA":
            try:
                transaction = get_data_state.run()
                if transaction is None:
                    log_print("[MAIN] No records available — waiting 10s before retry")
                    #use config
                    time.sleep(config.TIMEOUT_NO_RECORDS)

                    get_data_state.reset()
                    state = "GET_DATA"
                else:
                    transaction_number += 1
                    state = "PROCESS"
            except config.SystemException as e:
                log_print(f"[MAIN] GET_DATA failed: {e}")
                retry_count += 1
                if retry_count < config.MAX_SYSTEM_RETRIES:
                    get_data_state.reset()
                    state = "INIT"
                else:
                    system_errors.append(str(e))
                    state = "END"

        elif state == "PROCESS":
            try:
                process_state.run(transaction, {})
                save_to_report(transaction, "Success")
                success_count += 1
                state = "GET_DATA"
            except config.BusinessRuleException as e:
                log_print(f"[MAIN] Business error #{transaction_number}: {e}")
                save_to_report(transaction, "Skipped", str(e))
                business_errors.append((transaction.get("patient_name", "?"), str(e)))
                get_data_state.reset()
                state = "GET_DATA"
            except config.SystemException as e:
                log_print(f"[MAIN] System error #{transaction_number}: {e}")
                save_to_report(transaction, "Failed", str(e))
                system_errors.append(str(e))
                retry_count += 1
                if retry_count < config.MAX_SYSTEM_RETRIES:
                    state = "INIT"
                else:
                    state = "END"

        elif state == "END":
            end_state.run(transaction_number, success_count, business_errors, system_errors)
            break
except KeyboardInterrupt:
    log_print("[MAIN] Stopped by user — Pioneer kept running")
    end_state.run(transaction_number, success_count, business_errors, system_errors, kill_app=False)
finally:
    stop_recording()
    close_log_queue_manager()
    close_log_file()
    print("[MAIN] Cleanup complete")
