"""
Pioneer Update Status API Module
Calls rpa_update_status.php for three outcomes: skipped, success, failed.
Only call when message_id is available (i.e. after xml_api.submit_xml succeeds).
"""
import base64
import time
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print

API_UPDATE_ENDPOINT = "https://portal.reuniterx.com/api/v1/webservice/endpoint/rpa_update_status.php"


def _call_update_api(payload, max_retries=config.MAX_API_RETRIES):
    """
    POST payload to the update status endpoint with retry logic.

    Args:
        payload: dict with message_id, completed, remark, e1_look_up,
                 new_patient_in_pionner, attachment
        max_retries: number of retry attempts

    Returns:
        bool: True if API acknowledged successfully
    """
    if not payload.get("message_id"):
        log_print("[UPDATE API] Skipped — no message_id available")
        return False

    auth_string = base64.b64encode(
        f"{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}".encode()
    ).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_string}"
    }

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = 2 * (2 ** (attempt - 1))
                log_print(f"[UPDATE API] Retry {attempt + 1}/{max_retries} after {delay}s...")
                time.sleep(delay)

            response = requests.post(
                API_UPDATE_ENDPOINT, json=payload, headers=headers,
                timeout=config.API_TIMEOUT
            )

            result = response.json()
            status = str(result.get("status", "")).upper()
            log_print(f"[UPDATE API] Response: {result}")
            return status == "SUCCESS"

        except requests.exceptions.Timeout:
            log_print(f"[UPDATE API] Timeout (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            log_print(f"[UPDATE API] Request failed: {e} (attempt {attempt + 1}/{max_retries})")

    log_print(f"[UPDATE API] All {max_retries} attempts failed")
    return False


def update_skipped(message_id, remark="skipped"):
    """
    Mark Rx as skipped (transferrable=0 or drug/compound not found).

    Args:
        message_id: unique Rx identifier from xml_api response
        remark:     reason for skipping

    Returns:
        bool: True if acknowledged
    """
    payload = {
        "message_id": message_id,
        "completed": 0,
        "remark": remark,
        "e1_look_up": "0",
        "new_patient_in_pionner": "0",
        "attachment": ""
    }
    log_print(f"[UPDATE API] Sending SKIPPED — {remark}")
    return _call_update_api(payload)


def update_success(message_id, e1_look_up="0", new_patient_in_pioneer="0"):
    """
    Mark Rx as successfully completed.

    Args:
        message_id:            unique Rx identifier from xml_api response
        e1_look_up:            "1" if E1 lookup ran successfully, else "0"
        new_patient_in_pioneer: "1" if a new patient was added, else "0"

    Returns:
        bool: True if acknowledged
    """
    payload = {
        "message_id": message_id,
        "completed": 1,
        "remark": "success",
        "e1_look_up": e1_look_up,
        "new_patient_in_pionner": new_patient_in_pioneer,
        "attachment": ""
    }
    log_print(f"[UPDATE API] Sending SUCCESS")
    return _call_update_api(payload)


def update_failed(message_id, remark="failed"):
    """
    Mark Rx as failed due to an exception.

    Args:
        message_id: unique Rx identifier from xml_api response
        remark:     error description

    Returns:
        bool: True if acknowledged
    """
    payload = {
        "message_id": message_id,
        "completed": 0,
        "remark": remark[:500],   # cap length to avoid oversized payloads
        "e1_look_up": "0",
        "new_patient_in_pionner": "0",
        "attachment": ""
    }
    log_print(f"[UPDATE API] Sending FAILED — {remark}")
    return _call_update_api(payload)
