"""
End State - Close application, log summary report
"""
import sys
import os
import csv
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.helper import log_print
from modules import login


def run(processed=0, success_count=0, business_errors=None, system_errors=None, kill_app=True):
    """
    End the automation session.
    1. Close Pioneer (kill process) — only if kill_app=True
    2. Write summary report to CSV
    3. Print final stats

    Args:
        processed: Total transactions attempted
        success_count: Successful transactions
        business_errors: list of (patient_name, error_msg) tuples
        system_errors: list of error messages
        kill_app: Whether to kill Pioneer process (False when debugging)
    """
    business_errors = business_errors or []
    system_errors = system_errors or []

    log_print("=" * 60)
    log_print("[END] Closing automation session")
    log_print("=" * 60)

    if kill_app:
        try:
            login.kill_pioneer()
        except Exception:
            pass

    # Write report
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    report_file = os.path.join(
        config.REPORTS_DIR,
        f"report_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    )

    try:
        with open(report_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Detail"])
            writer.writerow(["Total Processed", processed])
            writer.writerow(["Successful", success_count])
            writer.writerow(["Business Errors", len(business_errors)])
            writer.writerow(["System Errors", len(system_errors)])
            writer.writerow([])
            for patient, msg in business_errors:
                writer.writerow(["BRE", f"{patient}: {msg}"])
            for msg in system_errors:
                writer.writerow(["SYS", msg])
        log_print(f"[END] Report saved: {report_file}")
    except Exception as e:
        log_print(f"[END] Failed to write report: {e}")

    # Print summary
    log_print(f"\n{'=' * 40}")
    log_print(f"  Total Processed : {processed}")
    log_print(f"  Successful      : {success_count}")
    log_print(f"  Business Errors : {len(business_errors)}")
    log_print(f"  System Errors   : {len(system_errors)}")
    log_print(f"{'=' * 40}")
    log_print("[END] Session complete")
