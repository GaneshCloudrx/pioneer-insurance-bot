"""
Get Data State - Download queue, process file, claim next prescription from API
Returns transaction dict or None if no more items
"""
import sys
import os
from pywinauto.keyboard import send_keys
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.helper import log_print
from modules import queue_download, unique_prescription

# Module-level state to track current queue
_queue_df = None
_queue_downloaded = False


def run():
    """
    Get next transaction item to process.
    1. Download queue export (first call only)
    2. Process queue file
    3. Claim next available prescription via API

    Returns:
        dict: Transaction data with keys (index, unique_string, api_id, patient_name, priority)
              or None if no more items

    Raises:
        config.SystemException: If download or file processing fails
    """
    global _queue_df, _queue_downloaded

    log_print("=" * 60)
    log_print("[GET_DATA] Getting next transaction")
    log_print("=" * 60)

    now = datetime.now()
    if (now.hour, now.minute) >= (config.BOT_STOP_HOUR, config.BOT_STOP_MINUTE):
        log_print(f"[GET_DATA] Stop time reached ({config.BOT_STOP_HOUR}:{config.BOT_STOP_MINUTE:02d}) — ending session")
        raise config.SystemException("Stop time reached")

    # Step 1: Download queue (only once per session)
    if not _queue_downloaded:
        # lets clear all available pop ups before downloading queue by using escapte keys two times   
        
        send_keys("{ESC}")
        time.sleep(0.5)
        send_keys("{ESC}")
        success, file_path = queue_download.download_queue()
        if not success:
            raise config.SystemException("Failed to download queue")

        # Step 2: Process queue file
        success, df, count = unique_prescription.process_queue_file(file_path)
        os.remove(file_path)
        if not success:
            raise config.SystemException("Failed to process queue file")

        if count == 0:
            log_print("[GET_DATA] No prescriptions in queue")
            return None

        _queue_df = df
        _queue_downloaded = True
        log_print(f"[GET_DATA] Queue loaded: {count} prescriptions")

    # Step 3: Claim next prescription from API
    success, index, unique_string, api_id, patient_name, priority = \
        unique_prescription.unique_prescription_from_queue_api(
            _queue_df, config.PIONEER_USERNAME, config.RETRY_FILE_PATH
        )

    if not success or index == -1:
        log_print("[GET_DATA] No more prescriptions to claim")
        return None

    transaction = {
        "index": index,
        "unique_string": unique_string,
        "api_id": api_id,
        "patient_name": patient_name,
        "priority": priority
    }
    log_print(f"[GET_DATA] Claimed: {patient_name} | API ID: {api_id}")
    return transaction


def reset():
    """Reset queue state for re-download on next run."""
    global _queue_df, _queue_downloaded
    _queue_df = None
    _queue_downloaded = False
