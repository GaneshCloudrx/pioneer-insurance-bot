"""
End State - Summary and cleanup for Insurance Bot
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def run(total_processed, success_count, business_errors, system_errors):
    """
    Print summary of the processing session.

    Args:
        total_processed: Total number of patients attempted
        success_count: Number of successful completions
        business_errors: List of (patient, error) tuples
        system_errors: List of error strings
    """
    log_print("=" * 60)
    log_print("[END] Session Summary")
    log_print("=" * 60)
    log_print(f"  Total Processed: {total_processed}")
    log_print(f"  Successful:      {success_count}")
    log_print(f"  Business Errors: {len(business_errors)}")
    log_print(f"  System Errors:   {len(system_errors)}")

    if business_errors:
        log_print("\n  Business Errors:")
        for patient, error in business_errors:
            log_print(f"    - {patient}: {error}")

    if system_errors:
        log_print("\n  System Errors:")
        for error in system_errors:
            log_print(f"    - {error}")

    log_print("=" * 60)
